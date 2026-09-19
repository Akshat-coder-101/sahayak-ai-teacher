import os
import re
import json
import logging
import hashlib
import urllib.parse
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import httpx

from ..config import settings
from ..database import SessionLocal, DBYouTubeCache, get_utc_now
from .llm import LLMService

logger = logging.getLogger("sahayak.youtube")

def parse_iso8601_duration(duration_str: str) -> str:
    """Parses ISO-8601 duration (e.g. PT12M34S, PT1H2M3S) into human-readable mm:ss or hh:mm:ss format."""
    if not duration_str:
        return ""
    match = re.match(r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$", duration_str)
    if not match:
        return ""
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

class YouTubeService:
    """
    AI-Grounded YouTube service that retrieves only real, validated videos
    via YouTube Data API v3 and caches results in SQLite to conserve quota.
    The LLM is strictly used for query synthesis and re-ranking, never inventing URLs.
    """

    @classmethod
    def _get_cache_key(cls, topic: str, language: str) -> str:
        norm_topic = " ".join(topic.lower().strip().split())
        norm_lang = (language or "en").lower().strip()
        return hashlib.sha256(f"{norm_topic}|{norm_lang}".encode("utf-8")).hexdigest()

    @classmethod
    def _read_cache(cls, cache_key: str) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            row = db.query(DBYouTubeCache).filter(DBYouTubeCache.key == cache_key).first()
            if not row:
                return None
            
            age_seconds = (get_utc_now() - row.created_at.replace(tzinfo=timezone.utc if row.created_at.tzinfo is None else None)).total_seconds()
            ttl_seconds = settings.YOUTUBE_CACHE_TTL_HOURS * 3600
            
            if age_seconds <= ttl_seconds:
                data = json.loads(row.payload)
                return {
                    "source": "cache",
                    "videos": data.get("videos", []),
                    "search_url": data.get("search_url", "")
                }
            return None
        except Exception as e:
            logger.warning(f"Failed to read YouTube cache: {e}")
            return None
        finally:
            db.close()

    @classmethod
    def _write_cache(cls, cache_key: str, videos: List[Dict[str, Any]], search_url: str):
        db = SessionLocal()
        try:
            payload = json.dumps({"videos": videos, "search_url": search_url})
            existing = db.query(DBYouTubeCache).filter(DBYouTubeCache.key == cache_key).first()
            if existing:
                existing.payload = payload
                existing.created_at = get_utc_now()
            else:
                new_entry = DBYouTubeCache(
                    key=cache_key,
                    payload=payload,
                    created_at=get_utc_now()
                )
                db.add(new_entry)
            db.commit()
        except Exception as e:
            logger.warning(f"Failed to write YouTube cache: {e}")
            db.rollback()
        finally:
            db.close()

    @classmethod
    async def _generate_search_query(cls, topic: str, language: str, segment_context: Optional[str]) -> str:
        """Uses LLM to synthesize a clean, high-precision educational search query."""
        try:
            prompt = (
                f"Topic: {topic}\n"
                f"Language: {language}\n"
                f"Context: {segment_context or 'Introductory explanation'}\n\n"
                "Formulate a single concise YouTube educational search query (3-6 words) that will find the highest quality concept explainer video. "
                "Respond in JSON format: {\"query\": \"...\"}"
            )
            res = await LLMService.generate_json(
                system_prompt="You are an expert curriculum curator. Return only JSON with a search query.",
                user_prompt=prompt,
                schema_hint='{"query": "concise search query"}',
                temperature=0.2
            )
            if res and isinstance(res, dict) and res.get("query"):
                return res["query"].strip()
        except Exception as e:
            logger.info(f"LLM query synthesis skipped/fallback: {e}")
        
        # Fallback to topic directly
        if language in ["hi", "hinglish"]:
            return f"{topic} explanation in hindi"
        elif language == "ta":
            return f"{topic} explanation in tamil"
        return f"{topic} concept explained"

    @classmethod
    def _fallback_search_url(cls, topic: str, language: str) -> str:
        """Pure helper to build stable, locale-matched YouTube search URL."""
        lang = (language or "en").lower().strip()
        q = (topic or "").strip()
        if lang == "hi":
            q = f"{q} हिंदी"  # Devanagari hint biases to Hindi results
            params = {"search_query": q, "hl": "hi", "gl": "IN"}
        elif lang == "hinglish":
            params = {"search_query": q, "hl": "hi", "gl": "IN"}  # English term + Hindi locale => Hinglish channels
        elif lang == "ta":
            q = f"{q} தமிழ்"  # Tamil script hint biases to Tamil results
            params = {"search_query": q, "hl": "ta", "gl": "IN"}
        else:  # en (default)
            params = {"search_query": q, "hl": "en"}
        return "https://www.youtube.com/results?" + urllib.parse.urlencode(params)

    @classmethod
    async def find_videos(
        cls,
        *,
        topic: str,
        language: str = "en",
        segment_context: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Retrieves real, validated YouTube videos with graceful fallbacks.
        Guarantees 0 fabricated video IDs and returns 0-cost search URL when no API key is available.
        """
        clean_topic = (topic or "").strip()
        if not clean_topic:
            clean_topic = "Science and Mathematics"

        norm_lang = (language or "en").lower().strip()
        fallback_search_url = cls._fallback_search_url(clean_topic, norm_lang)
        
        limit = max_results or settings.YOUTUBE_MAX_RESULTS

        # 1. No Key Provided -> Return honest fallback search URL (never fake IDs)
        if not settings.YOUTUBE_API_KEY or settings.YOUTUBE_API_KEY.startswith("your_"):
            return {
                "source": "fallback",
                "videos": [],
                "search_url": fallback_search_url
            }

        cache_key = cls._get_cache_key(clean_topic, norm_lang)

        # 2. Check Local Database Cache
        cached_result = cls._read_cache(cache_key)
        if cached_result:
            return cached_result

        # 3. Formulate Search Query with LLM (guarded)
        query = await cls._generate_search_query(clean_topic, norm_lang, segment_context)

        # 4. Call YouTube Data API v3 search.list
        video_ids = []
        try:
            search_params: Dict[str, Any] = {
                "key": settings.YOUTUBE_API_KEY,
                "part": "snippet",
                "q": query,
                "type": "video",
                "videoEmbeddable": "true",
                "safeSearch": "strict",
                "maxResults": limit * 2,  # Request extra to account for validation filtering
            }
            if norm_lang in ["hi", "hinglish"]:
                search_params["relevanceLanguage"] = "hi"
                search_params["regionCode"] = "IN"
            elif norm_lang == "ta":
                search_params["relevanceLanguage"] = "ta"
                search_params["regionCode"] = "IN"
            elif norm_lang == "te":
                search_params["relevanceLanguage"] = "te"
                search_params["regionCode"] = "IN"
            elif norm_lang == "bn":
                search_params["relevanceLanguage"] = "bn"
                search_params["regionCode"] = "IN"
            elif norm_lang == "es":
                search_params["relevanceLanguage"] = "es"
            else:
                search_params["relevanceLanguage"] = "en"

            async with httpx.AsyncClient(timeout=8.0) as client:
                search_resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params=search_params
                )
                if search_resp.status_code == 200:
                    search_data = search_resp.json()
                    for item in search_data.get("items", []):
                        v_id = item.get("id", {}).get("videoId")
                        if v_id and len(v_id) == 11:
                            video_ids.append(v_id)
                elif search_resp.status_code == 403:
                    logger.warning(f"YouTube API Quota exceeded or forbidden: {search_resp.text}")
                    return {
                        "source": "fallback",
                        "videos": [],
                        "search_url": fallback_search_url
                    }
                else:
                    logger.warning(f"YouTube search.list non-200 [{search_resp.status_code}]: {search_resp.text}")
        except Exception as e:
            logger.warning(f"YouTube search network exception: {e}")
            return {
                "source": "fallback",
                "videos": [],
                "search_url": fallback_search_url
            }

        if not video_ids:
            return {
                "source": "fallback",
                "videos": [],
                "search_url": fallback_search_url
            }

        # 5. Validate videos.list (Embeddable, Public, Non-Age-Restricted)
        validated_videos = []
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                video_resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/videos",
                    params={
                        "key": settings.YOUTUBE_API_KEY,
                        "part": "status,contentDetails,snippet",
                        "id": ",".join(video_ids[:10])
                    }
                )
                if video_resp.status_code == 200:
                    video_data = video_resp.json()
                    for item in video_data.get("items", []):
                        status_obj = item.get("status", {})
                        content_obj = item.get("contentDetails", {})
                        snippet_obj = item.get("snippet", {})
                        
                        # Validate embeddable, public, and safe
                        is_embeddable = status_obj.get("embeddable") is True
                        is_public = status_obj.get("privacyStatus") == "public"
                        is_not_age_restricted = content_obj.get("contentRating", {}).get("ytRating") != "ytAgeRestricted"

                        if is_embeddable and is_public and is_not_age_restricted:
                            vid_id = item.get("id")
                            duration_raw = content_obj.get("duration", "")
                            duration_formatted = parse_iso8601_duration(duration_raw)
                            
                            thumbs = snippet_obj.get("thumbnails", {})
                            thumb_url = (
                                thumbs.get("high", {}).get("url") or
                                thumbs.get("medium", {}).get("url") or
                                thumbs.get("default", {}).get("url") or
                                f"https://i.ytimg.com/vi/{vid_id}/hqdefault.jpg"
                            )

                            validated_videos.append({
                                "video_id": vid_id,
                                "title": snippet_obj.get("title", f"Video for {clean_topic}"),
                                "channel": snippet_obj.get("channelTitle", "YouTube Educator"),
                                "thumbnail_url": thumb_url,
                                "embed_url": f"https://www.youtube-nocookie.com/embed/{vid_id}",
                                "watch_url": f"https://www.youtube.com/watch?v={vid_id}",
                                "duration": duration_formatted or "Video"
                            })
                            if len(validated_videos) >= limit:
                                break
        except Exception as e:
            logger.warning(f"YouTube videos.list validation exception: {e}")

        # If validation yielded real videos, cache and return
        if validated_videos:
            cls._write_cache(cache_key, validated_videos, fallback_search_url)
            return {
                "source": "youtube",
                "videos": validated_videos,
                "search_url": fallback_search_url
            }

        return {
            "source": "fallback",
            "videos": [],
            "search_url": fallback_search_url
        }
