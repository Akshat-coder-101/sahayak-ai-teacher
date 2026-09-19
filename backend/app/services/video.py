import os
import shutil
import logging
import subprocess
import math
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..config import settings
from .tts import TTSService

logger = logging.getLogger("sahayak.video")

class VideoService:
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
        duration_sec = 6.0

        if audio_url and audio_url.startswith("/media/"):
            audio_filename = os.path.basename(audio_url)
            possible_path = os.path.join(media_dir, audio_filename)
            if not (os.path.exists(possible_path) and os.path.getsize(possible_path) > 0):
                audio_filename = None

        if not audio_filename:
            try:
                tts_res = await TTSService.generate_speech(script, language=language)
                if tts_res.get("audio_url") and tts_res["audio_url"].startswith("/media/"):
                    audio_filename = os.path.basename(tts_res["audio_url"])
                    possible_path = os.path.join(media_dir, audio_filename)
                    if os.path.exists(possible_path) and os.path.getsize(possible_path) > 0:
                        duration_sec = float(tts_res.get("duration_seconds") or 6.0)
                    else:
                        audio_filename = None
            except Exception as e:
                logger.warning(f"[VideoService] Audio generation for video failed: {e}")

        if not audio_filename:
            logger.warning("[VideoService] No audio track available for video synthesis.")
            return {
                "provider": "ffmpeg_local",
                "status": "unavailable",
                "video_url": None,
                "duration_sec": 0.0
            }

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
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=media_dir, timeout=25)
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
            res_fb = subprocess.run(fb_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=media_dir, timeout=15)
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
    async def export_full_lesson_video(cls, job_id: str, session_id: str) -> None:
        """
        Background worker that synthesizes and stitches all lesson segments into a unified MP4 export.
        Updates DBExportJob status and progress atomically.
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
                return

            job.status = "processing"
            job.progress = 5
            db.commit()

            ffmpeg_bin = shutil.which("ffmpeg")
            if not ffmpeg_bin:
                job.status = "failed"
                job.error_message = "FFmpeg runtime binary not found on host. Please deploy with Docker or install ffmpeg."
                db.commit()
                logger.warning(f"[VideoService] Job {job_id} failed: ffmpeg binary missing.")
                return

            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            media_dir = os.path.join(backend_dir, settings.MEDIA_DIR)
            os.makedirs(media_dir, exist_ok=True)

            plan_data = sess.plan_json if isinstance(sess.plan_json, dict) else {}
            raw_segments = plan_data.get("segments", [])
            if not raw_segments:
                raw_segments = [{"id": 1, "concept": sess.topic, "visual_type": "labeled-diagram"}]

            total_segments = len(raw_segments)
            rendered_segment_files: List[str] = []

            for idx, raw_seg in enumerate(raw_segments):
                seg_id = raw_seg.get("id", idx + 1)
                
                # Render segment payload
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

                script = getattr(seg_render, "spoken_script", "") if seg_render else f"In this segment we examine {raw_seg.get('concept', 'Key Concept')}."
                visual_spec = getattr(seg_render, "visual_spec", None)
                v_dict = visual_spec.model_dump() if hasattr(visual_spec, "model_dump") else (visual_spec or {"title": raw_seg.get("concept", "Concept"), "type": "labeled-diagram"})
                captions = getattr(seg_render, "captions", []) if seg_render else []
                audio_url = getattr(seg_render, "audio_url", None) if seg_render else None

                # Synthesize individual segment video
                seg_res = await cls.render_segment_video(
                    segment_id=seg_id,
                    session_id=session_id,
                    script=script,
                    audio_url=audio_url,
                    visual_spec=v_dict,
                    captions=captions,
                    language=sess.language or "en"
                )

                if seg_res.get("status") == "ready" and seg_res.get("video_url"):
                    seg_filename = os.path.basename(seg_res["video_url"])
                    seg_full_path = os.path.join(media_dir, seg_filename)
                    if os.path.exists(seg_full_path):
                        rendered_segment_files.append(seg_full_path)

                job.progress = min(85, 10 + int(((idx + 1) / total_segments) * 75))
                db.commit()

            if not rendered_segment_files:
                job.status = "failed"
                job.error_message = "Could not synthesize segment video tracks: media components not found or ffmpeg unavailable."
                db.commit()
                return

            # Stitch all segment videos into final full-lesson MP4
            final_filename = f"export_{job_id}.mp4"
            final_path = os.path.join(media_dir, final_filename)

            if len(rendered_segment_files) == 1:
                shutil.copyfile(rendered_segment_files[0], final_path)
            else:
                concat_list_file = os.path.join(media_dir, f"concat_{job_id}.txt")
                with open(concat_list_file, "w", encoding="utf-8") as f:
                    for fpath in rendered_segment_files:
                        f.write(f"file '{os.path.basename(fpath)}'\n")

                concat_cmd = [
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
                res_concat = subprocess.run(concat_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=media_dir, timeout=60)
                if os.path.exists(concat_list_file):
                    os.remove(concat_list_file)

                if res_concat.returncode != 0 or not os.path.exists(final_path):
                    # Fallback copy first segment
                    shutil.copyfile(rendered_segment_files[0], final_path)

            job.status = "completed"
            job.progress = 100
            job.video_url = f"/media/{final_filename}"
            db.commit()
            logger.info(f"[VideoService] Export job {job_id} successfully finished: {job.video_url}")

        except Exception as err:
            logger.exception(f"[VideoService] Export job {job_id} encountered fatal error: {err}")
            try:
                job = db.query(DBExportJob).filter(DBExportJob.id == job_id).first()
                if job:
                    job.status = "failed"
                    job.error_message = str(err)
                    db.commit()
            except Exception:
                pass
        finally:
            db.close()
