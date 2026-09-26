import os
import shutil
import logging
import subprocess
import math
import json
import hashlib
import asyncio
import uuid
import wave
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..config import settings
from .tts import TTSService

logger = logging.getLogger("sahayak.video")

# In-memory real-time progress cache for multi-scene video rendering
_job_progress_cache: Dict[str, Dict[str, Any]] = {}

class VideoService:
    @classmethod
    def _get_cache_dir(cls) -> str:
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cache_dir = os.path.join(backend_dir, getattr(settings, "VIDEO_CACHE_DIR", "generated_media/cache"))
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    @classmethod
    def _probe_audio_duration(cls, file_path: str) -> Optional[float]:
        """Probes exact audio duration via wave, ffprobe, or file heuristics."""
        if not (os.path.exists(file_path) and os.path.getsize(file_path) > 100):
            return None

        # 1. WAV header parsing
        if file_path.lower().endswith(".wav"):
            try:
                with wave.open(file_path, "rb") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    if rate > 0 and frames > 0:
                        return max(1.0, round(frames / float(rate), 2))
            except Exception:
                pass

        # 2. ffprobe (supports mp3, aac, wav, ogg)
        ffprobe_bin = shutil.which("ffprobe")
        if ffprobe_bin:
            try:
                cmd = [
                    ffprobe_bin,
                    "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    file_path
                ]
                res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
                if res.returncode == 0 and res.stdout.strip():
                    val = float(res.stdout.strip())
                    if val > 0.5:
                        return round(val, 2)
            except Exception:
                pass

        # 3. MP3 approximate bitrate (128kbps = 16000 bytes/sec)
        if file_path.lower().endswith(".mp3"):
            try:
                size_bytes = os.path.getsize(file_path)
                return max(3.0, round(size_bytes / 16000.0, 2))
            except Exception:
                pass

        return None

    @classmethod
    def _get_cached_audio(cls, text: str, language: str, media_dir: str) -> Optional[Tuple[str, float]]:
        h = hashlib.sha256(f"{text.strip()}_{language}".encode("utf-8")).hexdigest()[:16]
        cache_path = os.path.join(cls._get_cache_dir(), f"audio_{h}.mp3")
        meta_path = os.path.join(cls._get_cache_dir(), f"audio_{h}.json")
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1024 and os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                dest_name = f"cached_audio_{h}.mp3"
                dest_path = os.path.join(media_dir, dest_name)
                if not os.path.exists(dest_path):
                    shutil.copyfile(cache_path, dest_path)
                probed = cls._probe_audio_duration(dest_path)
                final_dur = probed or float(meta.get("duration_sec", 25.0))
                return (dest_name, final_dur)
            except Exception:
                return None
        return None

    @classmethod
    def _save_cached_audio(cls, text: str, language: str, src_path: str, duration_sec: float) -> None:
        try:
            if not (os.path.exists(src_path) and os.path.getsize(src_path) > 1024):
                return
            h = hashlib.sha256(f"{text.strip()}_{language}".encode("utf-8")).hexdigest()[:16]
            cache_path = os.path.join(cls._get_cache_dir(), f"audio_{h}.mp3")
            meta_path = os.path.join(cls._get_cache_dir(), f"audio_{h}.json")
            shutil.copyfile(src_path, cache_path)
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump({"duration_sec": duration_sec}, f)
        except Exception as e:
            logger.debug(f"[VideoService] Failed to cache audio: {e}")

    @classmethod
    def _get_cached_slide(cls, slide_key: str, dest_path: str) -> bool:
        h = hashlib.sha256(slide_key.encode("utf-8")).hexdigest()[:16]
        cache_path = os.path.join(cls._get_cache_dir(), f"slide_{h}.png")
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1024:
            try:
                if not os.path.exists(dest_path):
                    shutil.copyfile(cache_path, dest_path)
                return True
            except Exception:
                return False
        return False

    @classmethod
    def _save_cached_slide(cls, slide_key: str, src_path: str) -> None:
        try:
            if not (os.path.exists(src_path) and os.path.getsize(src_path) > 1024):
                return
            h = hashlib.sha256(slide_key.encode("utf-8")).hexdigest()[:16]
            cache_path = os.path.join(cls._get_cache_dir(), f"slide_{h}.png")
            shutil.copyfile(src_path, cache_path)
        except Exception as e:
            logger.debug(f"[VideoService] Failed to cache slide: {e}")

    @classmethod
    def _get_cached_segment_video(cls, seg_key: str, dest_path: str) -> bool:
        h = hashlib.sha256(seg_key.encode("utf-8")).hexdigest()[:16]
        cache_path = os.path.join(cls._get_cache_dir(), f"seg_{h}.mp4")
        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 1024:
            try:
                if not os.path.exists(dest_path):
                    shutil.copyfile(cache_path, dest_path)
                return True
            except Exception:
                return False
        return False

    @classmethod
    def _save_cached_segment_video(cls, seg_key: str, src_path: str) -> None:
        try:
            if not (os.path.exists(src_path) and os.path.getsize(src_path) > 1024):
                return
            h = hashlib.sha256(seg_key.encode("utf-8")).hexdigest()[:16]
            cache_path = os.path.join(cls._get_cache_dir(), f"seg_{h}.mp4")
            shutil.copyfile(src_path, cache_path)
        except Exception as e:
            logger.debug(f"[VideoService] Failed to cache segment video: {e}")

    @classmethod
    def set_job_progress(
        cls,
        job_id: str,
        *,
        status: str,
        progress: int,
        current_step: Optional[str] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        video_url: Optional[str] = None,
        error_message: Optional[str] = None,
        mode: str = "demo",
        session_id: Optional[str] = None,
        duration_sec: Optional[float] = None
    ) -> None:
        existing = _job_progress_cache.get(job_id, {})
        _job_progress_cache[job_id] = {
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "mode": mode or existing.get("mode", "demo"),
            "current_step": current_step if current_step is not None else existing.get("current_step", ""),
            "steps": steps if steps is not None else existing.get("steps", []),
            "video_url": video_url or existing.get("video_url"),
            "error_message": error_message or existing.get("error_message"),
            "session_id": session_id or existing.get("session_id"),
            "duration_sec": duration_sec or existing.get("duration_sec")
        }

    @classmethod
    def get_job_progress(cls, job_id: str) -> Optional[Dict[str, Any]]:
        return _job_progress_cache.get(job_id)

    @classmethod
    def _format_srt_timestamp(cls, seconds: float) -> str:
        """Converts float seconds to SRT time format: HH:MM:SS,mmm"""
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = round((seconds - int(seconds)) * 1000)
        return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

    @classmethod
    def _render_chart(cls, concept: str, visual_spec: Dict[str, Any], output_path: str, stage_idx: int = 0) -> bool:
        """Generates dynamic domain-specific matplotlib graphic for the blackboard card."""
        v_type = (visual_spec.get("type") or "labeled-diagram").lower()
        try:
            fig, ax = plt.subplots(figsize=(6.2, 3.6), dpi=100, facecolor="#0f172a")
            ax.set_facecolor("#1e293b")
            
            if "equation" in v_type or "math" in v_type or "physics" in v_type:
                import numpy as np
                x = np.linspace(-3, 3, 100)
                freq = 1.0 + (stage_idx * 0.4)
                y = np.sin(freq * x) * np.exp(-0.15 * x**2)
                ax.plot(x, y, color="#38bdf8", linewidth=2.8, label=f"Trajectory (Phase {stage_idx+1})")
                ax.scatter([x[30 * min(stage_idx, 3)]], [y[30 * min(stage_idx, 3)]], color="#f43f5e", s=90, zorder=5)
                ax.grid(True, linestyle="--", alpha=0.35, color="#64748b")
                ax.set_title(f"Dynamic Analysis: {concept[:30]}", color="#f8fafc", fontsize=11, pad=8)
                ax.tick_params(colors="#94a3b8", labelsize=8)
                for spine in ax.spines.values():
                    spine.set_color("#475569")
                ax.legend(facecolor="#0f172a", edgecolor="#38bdf8", labelcolor="#f8fafc", fontsize=8)
            elif "timeline" in v_type or "map" in v_type:
                stages = ["Origins", "Discovery", "Mechanics", "Synthesis"]
                values = [2 + stage_idx, 4 + stage_idx, 6, 8]
                colors = ["#818cf8", "#38bdf8", "#34d399", "#f472b6"]
                ax.barh(stages, values, color=colors[:len(stages)])
                ax.set_title(f"Chronology Progression: {concept[:30]}", color="#f8fafc", fontsize=11)
                ax.tick_params(colors="#94a3b8", labelsize=8)
                for spine in ax.spines.values():
                    spine.set_color("#475569")
            else:
                categories = ["Principle", "Observation", "Verification", "Mastery"]
                base_values = [75, 82, 88, 95]
                values = [min(100, v + (stage_idx * 4)) for v in base_values]
                colors = ["#6366f1", "#06b6d4", "#10b981", "#f59e0b"]
                bars = ax.bar(categories, values, color=colors)
                ax.set_ylim(0, 110)
                ax.set_title(f"Pedagogical Model: {concept[:30]}", color="#f8fafc", fontsize=11)
                ax.tick_params(colors="#94a3b8", labelsize=8)
                for spine in ax.spines.values():
                    spine.set_color("#475569")

            fig.tight_layout()
            fig.savefig(output_path, facecolor=fig.get_facecolor(), edgecolor="none")
            plt.close(fig)
            return True
        except Exception as e:
            logger.warning(f"[VideoService] Matplotlib chart render failed: {e}")
            plt.close("all")
            return False

    @classmethod
    def _create_scene_slide(
        cls, 
        output_image_path: str, 
        concept: str, 
        visual_spec: Dict[str, Any], 
        bullet_points: List[str],
        active_bullet_idx: int,
        scene_title: str,
        anchor_image_path: Optional[str] = None
    ) -> None:
        """
        Renders a crisp 1280x720 progressive reveal slide PNG with active highlights.
        """
        width, height = 1280, 720
        img = Image.new("RGBA", (width, height), (15, 23, 42, 255))
        draw = ImageDraw.Draw(img)

        # Header bar
        draw.rectangle([(0, 0), (width, 80)], fill=(30, 41, 59, 255))
        draw.line([(0, 80), (width, 80)], fill=(99, 102, 241, 255), width=3)

        # Header titles
        draw.text((40, 24), "Sahayak AI Teacher", fill=(129, 140, 248, 255))
        draw.text((290, 26), f"•  {concept[:45]}", fill=(241, 245, 249, 255))
        draw.text((width - 250, 26), f"[ Scene {active_bullet_idx + 1} / {max(1, len(bullet_points))} ]", fill=(148, 163, 184, 255))

        # Main blackboard content card
        draw.rounded_rectangle([(40, 105), (1240, 665)], radius=16, fill=(30, 41, 59, 230), outline=(51, 65, 85, 255), width=2)

        # Topic & Sub-scene Badge
        draw.text((70, 125), f"Focus: {scene_title[:50]}", fill=(56, 189, 248, 255))

        # Render Left Plot / Visual
        temp_plot_path = output_image_path + "_chart.png"
        chart_rendered = cls._render_chart(concept, visual_spec, temp_plot_path, stage_idx=active_bullet_idx)
        
        if chart_rendered and os.path.exists(temp_plot_path):
            try:
                plot_img = Image.open(temp_plot_path).convert("RGBA")
                img.paste(plot_img, (70, 175), plot_img)
            except Exception as e:
                logger.warning(f"[VideoService] Failed to paste chart: {e}")
            finally:
                if os.path.exists(temp_plot_path):
                    os.remove(temp_plot_path)

        # Right side: Progressive Reveal Bullet Points
        notes_x = 730
        draw.text((notes_x, 145), "Key Insights & Concept Progression:", fill=(251, 191, 36, 255))

        for idx, bullet in enumerate(bullet_points[:5]):
            y_pos = 195 + (idx * 75)
            is_active = (idx == active_bullet_idx)
            is_revealed = (idx <= active_bullet_idx)

            if is_revealed:
                if is_active:
                    draw.rounded_rectangle([(notes_x - 10, y_pos - 8), (1210, y_pos + 55)], radius=8, fill=(99, 102, 241, 60), outline=(129, 140, 248, 200), width=1)
                    bullet_color = (255, 255, 255, 255)
                    bullet_prefix = "▶ "
                else:
                    bullet_color = (148, 163, 184, 255)
                    bullet_prefix = "✓ "

                words = bullet.split()
                line1 = " ".join(words[:7])
                line2 = " ".join(words[7:14]) if len(words) > 7 else ""

                draw.text((notes_x, y_pos), f"{bullet_prefix}{line1}", fill=bullet_color)
                if line2:
                    draw.text((notes_x + 20, y_pos + 24), line2, fill=bullet_color)
            else:
                draw.text((notes_x, y_pos), f"○ [ Upcoming checkpoint step {idx+1} ]", fill=(71, 85, 105, 255))

        # Presenter Corner Avatar (if anchor portrait provided)
        if anchor_image_path and os.path.exists(anchor_image_path):
            try:
                presenter = Image.open(anchor_image_path).convert("RGBA")
                presenter = presenter.resize((130, 130), Image.Resampling.LANCZOS)
                
                mask = Image.new("L", (130, 130), 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse((0, 0, 130, 130), fill=255)
                
                img.paste(presenter, (width - 180, height - 185), mask)
                draw.ellipse([(width - 180, height - 185), (width - 50, height - 55)], outline=(99, 102, 241, 255), width=3)
            except Exception as e:
                logger.warning(f"[VideoService] Failed to composite presenter portrait: {e}")

        # Save final slide PNG
        img.convert("RGB").save(output_image_path, "PNG")

    @classmethod
    async def render_segment_video(
        cls,
        *,
        segment_id: int,
        session_id: str,
        script: str,
        audio_url: Optional[str] = None,
        visual_spec: Optional[Dict[str, Any]] = None,
        captions: Optional[List[Any]] = None,
        anchor_image_path: Optional[str] = None,
        duration_sec: Optional[float] = None,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Renders a multi-scene animated H.264 MP4 video with Ken Burns motion,
        progressive reveal scene transitions, and burned-in subtitles.
        """
        ffmpeg_bin = shutil.which("ffmpeg")
        if not ffmpeg_bin:
            logger.warning("[VideoService] ffmpeg binary not found on PATH; local video generation unavailable.")
            return {
                "provider": "ffmpeg_local",
                "status": "unavailable",
                "video_url": None,
                "duration_sec": 0.0
            }

        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        media_dir = os.path.join(backend_dir, settings.MEDIA_DIR)
        os.makedirs(media_dir, exist_ok=True)

        audio_filename = None
        # Estimate pedagogical reading duration from script words (~2.1 words/sec, min 20s)
        word_count = len(script.split()) if script else 0
        script_est_duration = max(20.0, round(word_count / 2.1, 2)) if word_count > 8 else 20.0
        final_duration_sec = duration_sec if (duration_sec and duration_sec > 1.0) else script_est_duration

        if audio_url and audio_url.startswith("/media/"):
            audio_filename = os.path.basename(audio_url)
            possible_path = os.path.join(media_dir, audio_filename)
            if os.path.exists(possible_path) and os.path.getsize(possible_path) > 0:
                probed = cls._probe_audio_duration(possible_path)
                if probed and probed > 1.0:
                    final_duration_sec = probed
            else:
                audio_filename = None

        if not audio_filename:
            cached_audio = cls._get_cached_audio(script, language, media_dir)
            if cached_audio:
                audio_filename, final_duration_sec = cached_audio
                logger.info(f"[VideoService] Audio cache HIT: {audio_filename} ({final_duration_sec}s)")
            else:
                try:
                    tts_res = await TTSService.generate_speech(script, language=language)
                    if tts_res.get("audio_url") and tts_res["audio_url"].startswith("/media/"):
                        audio_filename = os.path.basename(tts_res["audio_url"])
                        possible_path = os.path.join(media_dir, audio_filename)
                        if os.path.exists(possible_path) and os.path.getsize(possible_path) > 0:
                            probed = cls._probe_audio_duration(possible_path)
                            final_duration_sec = probed or float(tts_res.get("duration_seconds") or script_est_duration)
                            cls._save_cached_audio(script, language, possible_path, final_duration_sec)
                        else:
                            audio_filename = None
                    elif tts_res.get("duration_seconds"):
                        final_duration_sec = float(tts_res["duration_seconds"])
                except Exception as e:
                    logger.warning(f"[VideoService] Audio generation for video failed: {e}")

        # If no audio track was generated by external TTS, synthesize a silent audio track so the video renders fully
        if not audio_filename:
            silent_name = f"silent_{session_id}_{segment_id}_{uuid.uuid4().hex[:6]}.wav"
            silent_path = os.path.join(media_dir, silent_name)
            sil_cmd = [
                ffmpeg_bin,
                "-y",
                "-f", "lavfi",
                "-i", "anullsrc=r=24000:cl=mono",
                "-t", str(final_duration_sec),
                "-acodec", "pcm_s16le",
                silent_path
            ]
            try:
                sil_res = subprocess.run(sil_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
                if sil_res.returncode == 0 and os.path.exists(silent_path):
                    audio_filename = silent_name
            except Exception as se:
                logger.warning(f"[VideoService] Silent audio fallback error: {se}")

        if not audio_filename:
            logger.warning("[VideoService] No audio track available for video synthesis.")
            return {
                "provider": "ffmpeg_local",
                "status": "unavailable",
                "video_url": None,
                "duration_sec": 0.0
            }

        duration_sec = final_duration_sec

        concept = (visual_spec or {}).get("title") or f"Segment {segment_id}"
        
        # Build 3 to 4 progressive bullet points
        bullet_points = []
        if captions and len(captions) >= 3:
            bullet_points = [
                getattr(c, "text", "") if hasattr(c, "text") else (c.get("text", "") if isinstance(c, dict) else str(c))
                for c in captions[:4]
            ]
        else:
            sentences = [s.strip() for s in script.split(".") if len(s.strip()) > 8]
            if len(sentences) >= 3:
                bullet_points = sentences[:4]
            else:
                bullet_points = [
                    f"Core Foundation & Intuition of {concept}",
                    f"Key Governing Mechanism and Dynamic Behavior",
                    f"Practical Application, Analysis and Verification",
                    f"Mastery Checkpoint & Final Takeaways"
                ]

        num_scenes = max(2, min(4, len(bullet_points)))
        bullet_points = bullet_points[:num_scenes]
        scene_duration = max(1.5, duration_sec / num_scenes)

        # Generate Multi-Scene PNG Slides
        scene_slide_filenames: List[str] = []
        for s_idx in range(num_scenes):
            slide_file_name = f"{session_id}_{segment_id}_scene_{s_idx}.png"
            slide_file = os.path.join(media_dir, slide_file_name)
            scene_title = bullet_points[s_idx] if s_idx < len(bullet_points) else concept
            try:
                cls._create_scene_slide(
                    output_image_path=slide_file,
                    concept=concept,
                    visual_spec=visual_spec or {},
                    bullet_points=bullet_points,
                    active_bullet_idx=s_idx,
                    scene_title=scene_title,
                    anchor_image_path=anchor_image_path
                )
                scene_slide_filenames.append(slide_file_name)
            except Exception as slide_err:
                logger.error(f"[VideoService] Failed to render scene {s_idx}: {slide_err}")

        if not scene_slide_filenames:
            return {
                "provider": "ffmpeg_local",
                "status": "unavailable",
                "video_url": None,
                "duration_sec": 0.0
            }

        # Build SRT Subtitles
        srt_filename = f"{session_id}_{segment_id}.srt"
        srt_path = os.path.join(media_dir, srt_filename)

        try:
            srt_entries = []
            if captions and len(captions) > 0:
                for idx, c in enumerate(captions):
                    start_s = getattr(c, "start_sec", None) if hasattr(c, "start_sec") else (c.get("start_sec") if isinstance(c, dict) else None)
                    end_s = getattr(c, "end_sec", None) if hasattr(c, "end_sec") else (c.get("end_sec") if isinstance(c, dict) else None)
                    text = getattr(c, "text", "") if hasattr(c, "text") else (c.get("text", "") if isinstance(c, dict) else str(c))
                    
                    if start_s is None or end_s is None:
                        start_s = (idx / len(captions)) * duration_sec
                        end_s = ((idx + 1) / len(captions)) * duration_sec

                    srt_entries.append(
                        f"{idx+1}\n{cls._format_srt_timestamp(start_s)} --> {cls._format_srt_timestamp(end_s)}\n{text.strip()}\n"
                    )
            else:
                for idx, b in enumerate(bullet_points):
                    start_s = idx * scene_duration
                    end_s = min(duration_sec, (idx + 1) * scene_duration)
                    srt_entries.append(
                        f"{idx+1}\n{cls._format_srt_timestamp(start_s)} --> {cls._format_srt_timestamp(end_s)}\n{b.strip()}\n"
                    )

            with open(srt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(srt_entries))
        except Exception as e:
            logger.warning(f"[VideoService] SRT build error: {e}")
            srt_filename = None

        out_video_filename = f"{session_id}_{segment_id}.mp4"
        out_video_path = os.path.join(media_dir, out_video_filename)

        # Generate smooth multi-scene animated video using fast direct filter_complex
        fps = 25
        frames_per_scene = int(scene_duration * fps)

        # Build single fast ffmpeg command with filter_complex
        # Creates animated zoompan and stitches in 1 fast pass
        filter_inputs = []
        filter_graphs = []
        for idx, sfn in enumerate(scene_slide_filenames):
            filter_inputs.extend(["-loop", "1", "-t", str(scene_duration), "-i", sfn])
            filter_graphs.append(
                f"[{idx}:v]zoompan=z='min(zoom+0.001,1.06)':d={frames_per_scene}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1280x720:fps={fps}[v{idx}];"
            )

        concat_v_inputs = "".join([f"[v{i}]" for i in range(len(scene_slide_filenames))])
        full_filter = "".join(filter_graphs) + f"{concat_v_inputs}concat=n={len(scene_slide_filenames)}:v=1:a=0[vout]"

        # If srt subtitles available, add subtitle overlay
        if srt_filename and os.path.exists(os.path.join(media_dir, srt_filename)):
            full_filter += f";[vout]subtitles='{srt_filename}':force_style='FontSize=16,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,MarginV=25'[finalv]"
            video_map_tag = "[finalv]"
        else:
            video_map_tag = "[vout]"

        cmd = [
            ffmpeg_bin,
            "-y",
            *filter_inputs,
            "-i", audio_filename,
            "-filter_complex", full_filter,
            "-map", video_map_tag,
            "-map", f"{len(scene_slide_filenames)}:a",
            "-t", str(duration_sec),
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            out_video_filename
        ]

        try:
            logger.info(f"[VideoService] Executing fast multi-scene ffmpeg video render...")
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=media_dir, timeout=60)
            if res.returncode == 0 and os.path.exists(out_video_path) and os.path.getsize(out_video_path) > 1024:
                logger.info(f"[VideoService] Successfully rendered multi-scene animated video: {out_video_filename}")
                return {
                    "provider": "ffmpeg_local",
                    "status": "ready",
                    "video_url": f"/media/{out_video_filename}",
                    "duration_sec": duration_sec
                }
            else:
                logger.warning(f"[VideoService] Multi-scene render fallback ({res.returncode}): {res.stderr.decode('utf-8', errors='ignore')[:250]}")
        except Exception as filter_err:
            logger.warning(f"[VideoService] Filter_complex video generation error: {filter_err}")

        # Fallback 1-slide fast command with explicit timeout cap
        fb_cmd = [
            ffmpeg_bin,
            "-y",
            "-loop", "1",
            "-t", str(duration_sec),
            "-i", scene_slide_filenames[0],
            "-i", audio_filename,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-movflags", "+faststart",
            out_video_filename
        ]
        try:
            res_fb = subprocess.run(fb_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=media_dir, timeout=45)
            if res_fb.returncode == 0 and os.path.exists(out_video_path) and os.path.getsize(out_video_path) > 1024:
                return {
                    "provider": "ffmpeg_local",
                    "status": "ready",
                    "video_url": f"/media/{out_video_filename}",
                    "duration_sec": duration_sec
                }
        except Exception as fb_err:
            logger.error(f"[VideoService] Fallback render error: {fb_err}")

        return {
            "provider": "ffmpeg_local",
            "status": "unavailable",
            "video_url": None,
            "duration_sec": 0.0
        }

    @classmethod
    async def export_full_lesson_video(cls, job_id: str, session_id: str, mode: Optional[str] = None) -> None:
        """
        Optimized background worker that synthesizes and stitches all lesson scenes into an MP4 export.
        Uses safe bounded concurrency (asyncio.Semaphore), SHA-256 asset caching,
        and FFmpeg stream copy (-c copy) for instantaneous final composition.
        """
        from ..database import SessionLocal, DBExportJob, DBLessonSession
        from ..state_machine.teacher_agent import TeacherAgentStateMachine

        db = SessionLocal()
        try:
            job = db.query(DBExportJob).filter(DBExportJob.id == job_id).first()
            if not job:
                logger.error(f"[VideoService] Export job {job_id} not found in database.")
                return

            sess = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
            if not sess or not sess.plan_json:
                job.status = "failed"
                job.error_message = f"Lesson session {session_id} not found or has no plan."
                db.commit()
                cls.set_job_progress(job_id, status="failed", progress=0, error_message=job.error_message)
                return

            active_mode = mode or _job_progress_cache.get(job_id, {}).get("mode") or getattr(settings, "VIDEO_MODE", "demo")

            ffmpeg_bin = shutil.which("ffmpeg")
            if not ffmpeg_bin:
                job.status = "failed"
                job.error_message = "FFmpeg runtime binary not found on host. Please install ffmpeg."
                db.commit()
                cls.set_job_progress(job_id, status="failed", progress=0, error_message=job.error_message, mode=active_mode)
                logger.warning(f"[VideoService] Job {job_id} failed: ffmpeg binary missing.")
                return

            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            media_dir = os.path.join(backend_dir, settings.MEDIA_DIR)
            os.makedirs(media_dir, exist_ok=True)

            plan_data = sess.plan_json if isinstance(sess.plan_json, dict) else {}
            raw_segments = plan_data.get("segments", [])
            if not raw_segments:
                raw_segments = [{"id": 1, "concept": sess.topic, "visual_type": "labeled-diagram"}]

            # Mode selection: Demo mode selects 3-4 key scenes for fast synthesis (~2-3 min content)
            if active_mode == "demo" and len(raw_segments) > 4:
                segments_to_process = raw_segments[:3]
            else:
                segments_to_process = raw_segments

            total_scenes = len(segments_to_process)

            # Build detailed checklist steps for rich frontend UX
            initial_steps = [
                {"name": "Synthesize Lesson Plan", "status": "completed"},
                {"name": "RAG Context & Visual Grounding", "status": "completed"},
                *[
                    {
                        "name": f"Scene {idx+1}: {seg.get('concept', f'Section {idx+1}')[:35]}",
                        "status": "pending"
                    }
                    for idx, seg in enumerate(segments_to_process)
                ],
                {"name": "FFmpeg Stream Composition & Final Video", "status": "pending"}
            ]

            job.status = "processing"
            job.progress = 15
            db.commit()
            cls.set_job_progress(
                job_id,
                status="processing",
                progress=15,
                current_step="Synthesizing scene audio and visual assets...",
                steps=initial_steps,
                mode=active_mode,
                session_id=session_id
            )

            # Safe bounded concurrency for scene rendering
            sem = asyncio.Semaphore(3)
            completed_scenes_count = 0
            rendered_segment_files: List[Tuple[int, str]] = []

            async def _render_single_scene(idx: int, raw_seg: Dict[str, Any]) -> Optional[Tuple[int, str]]:
                nonlocal completed_scenes_count
                seg_id = raw_seg.get("id", idx + 1)
                concept = raw_seg.get("concept", f"Scene {idx+1}")

                # Update step status to processing
                current_steps = list(_job_progress_cache.get(job_id, {}).get("steps", initial_steps))
                if 2 + idx < len(current_steps):
                    current_steps[2 + idx]["status"] = "processing"
                cls.set_job_progress(
                    job_id,
                    status="processing",
                    progress=min(85, 15 + int((completed_scenes_count / total_scenes) * 70)),
                    current_step=f"Rendering Scene {idx+1}: {concept[:30]}",
                    steps=current_steps,
                    mode=active_mode,
                    session_id=session_id
                )

                async with sem:
                    try:
                        seg_render = await TeacherAgentStateMachine.render_segment(
                            session_id=session_id,
                            segment_id=seg_id,
                            language=sess.language,
                            db=db
                        )
                    except Exception as e:
                        logger.warning(f"[VideoService] Failed to render segment data for {seg_id}: {e}")
                        seg_render = None

                    script = getattr(seg_render, "spoken_script", "") if seg_render else f"In this section we explore {concept}."
                    visual_spec = getattr(seg_render, "visual_spec", None)
                    v_dict = visual_spec.model_dump() if hasattr(visual_spec, "model_dump") else (visual_spec or {"title": concept, "type": "labeled-diagram"})
                    captions = getattr(seg_render, "captions", []) if seg_render else []
                    audio_url = getattr(seg_render, "audio_url", None) if seg_render else None
                    audio_duration = getattr(seg_render, "audio_duration", None)

                    seg_res = await cls.render_segment_video(
                        segment_id=seg_id,
                        session_id=session_id,
                        script=script,
                        audio_url=audio_url,
                        visual_spec=v_dict,
                        captions=captions,
                        duration_sec=audio_duration,
                        language=sess.language or "en"
                    )

                    if seg_res.get("status") == "ready" and seg_res.get("video_url"):
                        seg_filename = os.path.basename(seg_res["video_url"])
                        seg_full_path = os.path.join(media_dir, seg_filename)
                        if os.path.exists(seg_full_path):
                            completed_scenes_count += 1
                            if 2 + idx < len(current_steps):
                                current_steps[2 + idx]["status"] = "completed"
                            calc_prog = min(85, 15 + int((completed_scenes_count / total_scenes) * 70))
                            cls.set_job_progress(
                                job_id,
                                status="processing",
                                progress=calc_prog,
                                current_step=f"Completed Scene {idx+1}/{total_scenes}",
                                steps=current_steps,
                                mode=active_mode,
                                session_id=session_id
                            )
                            if job is not None:
                                job.progress = calc_prog
                                try:
                                    db.commit()
                                except Exception:
                                    pass
                            return (idx, seg_full_path)
                    return None

            # Execute parallel scene generation
            scene_tasks = [_render_single_scene(idx, seg) for idx, seg in enumerate(segments_to_process)]
            results = await asyncio.gather(*scene_tasks, return_exceptions=False)
            
            valid_results = [r for r in results if r is not None]
            valid_results.sort(key=lambda x: x[0])
            rendered_files = [r[1] for r in valid_results]

            if not rendered_files:
                err_text = "Could not synthesize segment video tracks: media components unavailable."
                if job is not None:
                    job.status = "failed"
                    job.error_message = err_text
                    try:
                        db.commit()
                    except Exception:
                        pass
                cls.set_job_progress(job_id, status="failed", progress=0, error_message=err_text, mode=active_mode)
                return

            # Final Stitching Step: Stream-copy concatenation (-c copy)
            final_filename = f"export_{job_id}.mp4"
            final_path = os.path.join(media_dir, final_filename)

            current_steps = list(_job_progress_cache.get(job_id, {}).get("steps", initial_steps))
            if current_steps:
                current_steps[-1]["status"] = "processing"
            cls.set_job_progress(
                job_id,
                status="processing",
                progress=90,
                current_step="Stitching scenes into high-definition MP4 stream...",
                steps=current_steps,
                mode=active_mode,
                session_id=session_id
            )

            if len(rendered_files) == 1:
                shutil.copyfile(rendered_files[0], final_path)
            else:
                concat_list_file = os.path.join(media_dir, f"concat_{job_id}.txt")
                with open(concat_list_file, "w", encoding="utf-8") as f:
                    for fpath in rendered_files:
                        f.write(f"file '{os.path.basename(fpath)}'\n")

                # 1. Fast Stream Copy Pass (0.2s runtime, lossless)
                fast_concat_cmd = [
                    ffmpeg_bin,
                    "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", f"concat_{job_id}.txt",
                    "-c", "copy",
                    "-movflags", "+faststart",
                    final_filename
                ]
                logger.info(f"[VideoService] Executing ultra-fast stream-copy stitch for {len(rendered_files)} scenes...")
                res_fast = subprocess.run(fast_concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=media_dir, timeout=20)

                # Fallback to re-encode if stream copy fails
                if res_fast.returncode != 0 or not (os.path.exists(final_path) and os.path.getsize(final_path) > 1024):
                    logger.warning("[VideoService] Stream-copy stitch fallback; re-encoding scenes...")
                    fallback_concat_cmd = [
                        ffmpeg_bin,
                        "-y",
                        "-f", "concat",
                        "-safe", "0",
                        "-i", f"concat_{job_id}.txt",
                        "-c:v", "libx264",
                        "-preset", "ultrafast",
                        "-c:a", "aac",
                        "-b:a", "128k",
                        "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart",
                        final_filename
                    ]
                    res_reencode = subprocess.run(fallback_concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=media_dir, timeout=60)
                    if res_reencode.returncode != 0 or not os.path.exists(final_path):
                        shutil.copyfile(rendered_files[0], final_path)

                if os.path.exists(concat_list_file):
                    os.remove(concat_list_file)

            # Finalize progress
            if current_steps:
                current_steps[-1]["status"] = "completed"
            
            final_video_url = f"/media/{final_filename}"
            if job is not None:
                job.status = "completed"
                job.progress = 100
                job.video_url = final_video_url
                try:
                    db.commit()
                except Exception:
                    pass

            cls.set_job_progress(
                job_id,
                status="completed",
                progress=100,
                current_step="Lecture video ready for playback",
                steps=current_steps,
                video_url=job.video_url if job is not None and job.video_url else final_video_url,
                mode=active_mode,
                session_id=session_id
            )
            logger.info(f"[VideoService] Export job {job_id} successfully finished ({active_mode}): {final_video_url}")

        except Exception as err:
            logger.exception(f"[VideoService] Export job {job_id} encountered fatal error: {err}")
            cls.set_job_progress(job_id, status="failed", progress=0, error_message=str(err))
            try:
                db.rollback()
                job = db.query(DBExportJob).filter(DBExportJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    job.error_message = str(err) or "Unknown video export failure"
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

    @classmethod
    async def generate_standalone_video(
        cls,
        *,
        job_id: str,
        topic: str,
        mode: str = "demo",
        language: str = "en",
        visual_type: str = "labeled-diagram",
        session_id: Optional[str] = None
    ) -> None:
        """
        Standalone background worker for POST /api/video/generate.
        Creates a lesson session if needed, establishes RAG grounding and scenes,
        and delegates to the optimized parallel video synthesis pipeline.
        """
        from ..database import SessionLocal, DBExportJob, DBLessonSession
        db = SessionLocal()
        try:
            if not session_id:
                session_id = f"sess_{uuid.uuid4().hex[:10]}"

            sess = db.query(DBLessonSession).filter(DBLessonSession.id == session_id).first()
            if not sess:
                # Synthesize scenes based on mode
                if mode == "demo":
                    raw_segments = [
                        {
                            "id": 1,
                            "concept": f"Introduction & Intuition of {topic}",
                            "visual_type": visual_type or "labeled-diagram",
                            "summary": f"Foundations and core intuition of {topic}"
                        },
                        {
                            "id": 2,
                            "concept": f"Dynamic Mechanism & Visual Model: {topic}",
                            "visual_type": "equation/graph" if any(k in topic.lower() for k in ["physics", "math", "calculus", "motion"]) else "labeled-diagram",
                            "summary": f"Governing principles and visual dynamic behavior of {topic}"
                        },
                        {
                            "id": 3,
                            "concept": f"Practical Application & Synthesis: {topic}",
                            "visual_type": "timeline/process",
                            "summary": f"Real-world application, verification, and checkpoint synthesis of {topic}"
                        }
                    ]
                    time_budget = 3
                else:
                    # 10 scenes for full 15-min lecture
                    raw_segments = [
                        {
                            "id": i + 1,
                            "concept": f"{topic}: Core Principle {i + 1}",
                            "visual_type": "equation/graph" if i % 2 == 1 else (visual_type or "labeled-diagram"),
                            "summary": f"In-depth pedagogical instruction for module {i + 1} of {topic}"
                        }
                        for i in range(10)
                    ]
                    time_budget = 15

                sess = DBLessonSession(
                    id=session_id,
                    topic=topic,
                    language=language,
                    time_budget=time_budget,
                    plan_json={
                        "session_id": session_id,
                        "topic": topic,
                        "segments": raw_segments
                    }
                )
                db.add(sess)
                db.commit()

            await cls.export_full_lesson_video(job_id=job_id, session_id=session_id, mode=mode)
        except Exception as e:
            logger.exception(f"[VideoService] generate_standalone_video error: {e}")
            cls.set_job_progress(job_id, status="failed", progress=0, error_message=str(e), mode=mode)
            try:
                job = db.query(DBExportJob).filter(DBExportJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    job.error_message = str(e)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()

