import os
import asyncio
import hashlib
import logging
import httpx
from typing import Dict, Any, Optional
from ..config import settings

logger = logging.getLogger("sahayak.avatar")

class AvatarService:
    DEFAULT_STOCK_AVATAR = "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?q=80&w=400&auto=format&fit=crop"

    @classmethod
    def get_anchor_portrait_path(cls) -> Optional[str]:
        """
        Returns the absolute local file path of a generated or cached anchor portrait if present.
        """
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        media_dir = os.path.join(backend_dir, settings.MEDIA_DIR)
        if not os.path.exists(media_dir):
            return None
        
        # Check for any generated avatar_*.png in MEDIA_DIR
        for f in sorted(os.listdir(media_dir)):
            if f.startswith("avatar_") and f.endswith(".png"):
                full_path = os.path.join(media_dir, f)
                if os.path.getsize(full_path) > 0:
                    return full_path
        return None

    @classmethod
    async def generate_avatar_video(
        cls, 
        script: str, 
        avatar_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Supports Colossyan, D-ID, HeyGen, Hugging Face SDXL, or built-in Interactive Canvas Avatar.
        """
        # 1. D-ID API (if key present and provider == 'did')
        if settings.DID_API_KEY and len(settings.DID_API_KEY.strip()) > 8 and settings.AVATAR_PROVIDER == "did":
            try:
                import base64
                raw_key = settings.DID_API_KEY.strip()
                if raw_key.startswith("Basic ") or raw_key.startswith("Bearer "):
                    auth_header = raw_key
                elif ":" in raw_key:
                    auth_header = f"Basic {base64.b64encode(raw_key.encode()).decode()}"
                else:
                    auth_header = f"Basic {base64.b64encode(f'{raw_key}:'.encode()).decode()}" if not raw_key.endswith("=") else f"Basic {raw_key}"

                source_img = settings.TEACHER_IMAGE_URL or (avatar_id if (avatar_id and avatar_id.startswith("http")) else cls.DEFAULT_STOCK_AVATAR)

                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(
                        "https://api.d-id.com/talks",
                        headers={
                            "Authorization": auth_header,
                            "Content-Type": "application/json"
                        },
                        json={
                            "script": {
                                "type": "text",
                                "input": script[:500],
                                "subtitles": "false"
                            },
                            "config": {"fluent": "false", "pad_audio": "0.0"},
                            "source_url": source_img
                        }
                    )
                    if resp.status_code in [200, 201]:
                        data = resp.json()
                        talk_id = data.get("id")
                        for _ in range(8):
                            await asyncio.sleep(2.0)
                            poll_res = await client.get(
                                f"https://api.d-id.com/talks/{talk_id}",
                                headers={"Authorization": auth_header}
                            )
                            if poll_res.status_code == 200:
                                p_data = poll_res.json()
                                if p_data.get("status") == "done":
                                    return {
                                        "provider": "did",
                                        "video_id": talk_id,
                                        "status": "ready",
                                        "video_url": p_data.get("result_url"),
                                        "avatar_name": "D-ID AI Teacher"
                                    }
                    else:
                        logger.warning(f"[AvatarService] D-ID API returned {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"[AvatarService] D-ID call failed: {e}")

        # 2. HeyGen API (if key present and provider == 'heygen')
        if settings.HEYGEN_API_KEY and len(settings.HEYGEN_API_KEY.strip()) > 10 and settings.AVATAR_PROVIDER == "heygen":
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(
                        "https://api.heygen.com/v2/video/generate",
                        headers={
                            "X-Api-Key": settings.HEYGEN_API_KEY,
                            "Content-Type": "application/json"
                        },
                        json={
                            "video_inputs": [{
                                "character": {"type": "avatar", "avatar_id": avatar_id or settings.AVATAR_DEFAULT_ID},
                                "voice": {"type": "text", "input_text": script[:600]}
                            }],
                            "test": False
                        }
                    )
                    if resp.status_code in [200, 201]:
                        data = resp.json()
                        vid_id = data.get("data", {}).get("video_id")
                        if vid_id:
                            for _ in range(6):
                                await asyncio.sleep(2.5)
                                poll_resp = await client.get(
                                    f"https://api.heygen.com/v1/video_status.get?video_id={vid_id}",
                                    headers={"X-Api-Key": settings.HEYGEN_API_KEY}
                                )
                                if poll_resp.status_code == 200:
                                    p_data = poll_resp.json().get("data", {})
                                    if p_data.get("status") == "completed":
                                        return {
                                            "provider": "heygen",
                                            "video_id": vid_id,
                                            "status": "ready",
                                            "video_url": p_data.get("video_url"),
                                            "avatar_name": "HeyGen AI Presenter"
                                        }
                        return {
                            "provider": "heygen",
                            "video_id": vid_id,
                            "status": "processing",
                            "video_url": None,
                            "avatar_name": "HeyGen AI Presenter"
                        }
            except Exception as e:
                logger.warning(f"[AvatarService] HeyGen call failed: {e}")

        # 3. Synthesia API (if key present and provider == 'synthesia')
        if settings.SYNTHESIA_API_KEY and len(settings.SYNTHESIA_API_KEY.strip()) > 10 and settings.AVATAR_PROVIDER == "synthesia":
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(
                        "https://api.synthesia.io/v2/videos",
                        headers={
                            "Authorization": settings.SYNTHESIA_API_KEY,
                            "Content-Type": "application/json"
                        },
                        json={
                            "title": "Sahayak AI Teacher Lesson Segment",
                            "description": "Auto-generated educational segment",
                            "visibility": "public",
                            "input": [{
                                "scriptText": script[:800],
                                "avatar": avatar_id or settings.AVATAR_DEFAULT_ID or "anna_costume1_cameraA",
                                "background": "green_screen"
                            }]
                        }
                    )
                    if resp.status_code in [200, 201]:
                        data = resp.json()
                        vid_id = data.get("id")
                        for _ in range(6):
                            await asyncio.sleep(3.0)
                            poll_resp = await client.get(
                                f"https://api.synthesia.io/v2/videos/{vid_id}",
                                headers={"Authorization": settings.SYNTHESIA_API_KEY}
                            )
                            if poll_resp.status_code == 200:
                                p_data = poll_resp.json()
                                if p_data.get("status") == "complete":
                                    return {
                                        "provider": "synthesia",
                                        "video_id": vid_id,
                                        "status": "ready",
                                        "video_url": p_data.get("download"),
                                        "avatar_name": "Synthesia AI Teacher"
                                    }
            except Exception as e:
                logger.warning(f"[AvatarService] Synthesia call failed: {e}")

        # 4. Tavus API (if key present and provider == 'tavus')
        if settings.TAVUS_API_KEY and len(settings.TAVUS_API_KEY.strip()) > 10 and settings.AVATAR_PROVIDER == "tavus":
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(
                        "https://tavusapi.com/v2/videos",
                        headers={
                            "x-api-key": settings.TAVUS_API_KEY,
                            "Content-Type": "application/json"
                        },
                        json={
                            "replica_id": settings.TAVUS_REPLICA_ID,
                            "script": script[:800],
                            "video_name": "Sahayak AI Video Lesson"
                        }
                    )
                    if resp.status_code in [200, 201]:
                        data = resp.json()
                        vid_id = data.get("video_id")
                        for _ in range(6):
                            await asyncio.sleep(2.5)
                            poll_resp = await client.get(
                                f"https://tavusapi.com/v2/videos/{vid_id}",
                                headers={"x-api-key": settings.TAVUS_API_KEY}
                            )
                            if poll_resp.status_code == 200:
                                p_data = poll_resp.json()
                                if p_data.get("status") == "ready":
                                    return {
                                        "provider": "tavus",
                                        "video_id": vid_id,
                                        "status": "ready",
                                        "video_url": p_data.get("download_url") or p_data.get("hosted_url"),
                                        "avatar_name": "Tavus Replica Teacher"
                                    }
            except Exception as e:
                logger.warning(f"[AvatarService] Tavus call failed: {e}")

        # 5. Colossyan API (if configured)
        if settings.COLOSSYAN_API_KEY and len(settings.COLOSSYAN_API_KEY.strip()) > 10 and settings.AVATAR_PROVIDER == "colossyan":
            try:
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(
                        "https://api.colossyan.com/v1/videos",
                        headers={
                            "Authorization": f"Bearer {settings.COLOSSYAN_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "title": "Sahayak AI Lesson Segment",
                            "actors": [{
                                "avatar": avatar_id or settings.AVATAR_DEFAULT_ID,
                                "script": script
                            }]
                        }
                    )
                    if resp.status_code in [200, 201]:
                        data = resp.json()
                        vid_id = data.get("id")
                        video_url = data.get("video_url")
                        
                        if vid_id and not video_url:
                            for _ in range(5):
                                await asyncio.sleep(2.0)
                                poll_resp = await client.get(
                                    f"https://api.colossyan.com/v1/videos/{vid_id}",
                                    headers={"Authorization": f"Bearer {settings.COLOSSYAN_API_KEY}"}
                                )
                                if poll_resp.status_code == 200:
                                    p_data = poll_resp.json()
                                    if p_data.get("status") in ["ready", "completed"]:
                                        video_url = p_data.get("video_url")
                                        break
                                        
                        return {
                            "provider": "colossyan",
                            "video_id": vid_id,
                            "status": "ready" if video_url else data.get("status", "processing"),
                            "video_url": video_url,
                            "avatar_name": "Colossyan AI Presenter"
                        }
            except Exception as e:
                logger.warning(f"[AvatarService] Colossyan failed: {e}")

        # 6. Replicate API (LivePortrait / SadTalker)
        if settings.REPLICATE_API_TOKEN and len(settings.REPLICATE_API_TOKEN.strip()) > 10 and settings.AVATAR_PROVIDER == "replicate":
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    source_img = settings.TEACHER_IMAGE_URL or cls.DEFAULT_STOCK_AVATAR
                    resp = await client.post(
                        "https://api.replicate.com/v1/predictions",
                        headers={
                            "Authorization": f"Token {settings.REPLICATE_API_TOKEN}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "version": "4691456d353da3836d5a86a60db882a8747f4d380eec9fe11ad1b262d1ec8625",
                            "input": {
                                "source_image": source_img,
                                "text": script[:500]
                            }
                        }
                    )
                    if resp.status_code in [200, 201]:
                        pred_data = resp.json()
                        pred_id = pred_data.get("id")
                        for _ in range(8):
                            await asyncio.sleep(2.5)
                            poll_res = await client.get(
                                f"https://api.replicate.com/v1/predictions/{pred_id}",
                                headers={"Authorization": f"Token {settings.REPLICATE_API_TOKEN}"}
                            )
                            if poll_res.status_code == 200:
                                p_data = poll_res.json()
                                if p_data.get("status") == "succeeded":
                                    output = p_data.get("output")
                                    video_url = output if isinstance(output, str) else (output[0] if isinstance(output, list) else None)
                                    return {
                                        "provider": "replicate",
                                        "video_id": pred_id,
                                        "status": "ready",
                                        "video_url": video_url,
                                        "avatar_name": "LivePortrait AI Teacher"
                                    }
            except Exception as e:
                logger.warning(f"[AvatarService] Replicate call failed: {e}")

        # 7. Free Hugging Face Avatar Inference API (SDXL Base 1.0)
        if settings.HUGGINGFACE_API_KEY and len(settings.HUGGINGFACE_API_KEY.strip()) > 5 and settings.AVATAR_PROVIDER == "huggingface":
            try:
                prompt = "Professional friendly university AI professor teacher portrait, crisp lighting, high quality, photorealistic, neutral classroom background, 8k resolution"
                prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
                filename = f"avatar_{prompt_hash}.png"
                
                backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                media_dir = os.path.join(backend_dir, settings.MEDIA_DIR)
                os.makedirs(media_dir, exist_ok=True)
                file_path = os.path.join(media_dir, filename)

                if os.path.exists(file_path) and os.path.getsize(file_path) > 1024:
                    return {
                        "provider": "huggingface",
                        "status": "ready",
                        "avatar_name": "Prof. Sahayak AI",
                        "avatar_avatar_url": f"/media/{filename}",
                        "is_animated_canvas": True,
                        "video_url": None
                    }

                endpoint = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
                headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
                payload = {"inputs": prompt}

                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(endpoint, headers=headers, json=payload)
                    if resp.status_code == 200 and len(resp.content) > 1024:
                        with open(file_path, "wb") as f:
                            f.write(resp.content)
                        logger.info(f"[AvatarService] Successfully generated and cached HuggingFace SDXL portrait to {filename}.")
                        return {
                            "provider": "huggingface",
                            "status": "ready",
                            "avatar_name": "Prof. Sahayak AI",
                            "avatar_avatar_url": f"/media/{filename}",
                            "is_animated_canvas": True,
                            "video_url": None
                        }
            except Exception as e:
                logger.warning(f"[AvatarService] HuggingFace SDXL avatar generation failed ({e}); using stock presenter fallback.")

        # 8. Dynamic Interactive Canvas Avatar (Zero-cost fallback)
        teacher_img = settings.TEACHER_IMAGE_URL or cls.DEFAULT_STOCK_AVATAR
        return {
            "provider": "interactive_canvas_avatar",
            "avatar_name": "Prof. Sahayak AI",
            "avatar_avatar_url": teacher_img,
            "status": "ready",
            "video_url": None,
            "is_animated_canvas": True
        }

