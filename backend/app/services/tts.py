import os
import uuid
import logging
import wave
import httpx
from typing import Dict, Any, Optional
from ..config import settings

# Safe conditional import of piper
try:
    import piper
    from piper.voice import PiperVoice
    HAS_PIPER = True
except ImportError:
    piper = None
    PiperVoice = None
    HAS_PIPER = False

logger = logging.getLogger("sahayak.tts")

class TTSService:
    _piper_voice = None
    _piper_model_path = None

    @classmethod
    def _get_media_storage_path(cls) -> str:
        # Resolve path relative to backend root
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        media_dir = os.path.join(base_dir, settings.MEDIA_DIR)
        os.makedirs(media_dir, exist_ok=True)
        return media_dir

    @classmethod
    def _get_models_storage_path(cls) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        models_dir = os.path.join(base_dir, "models", "piper")
        os.makedirs(models_dir, exist_ok=True)
        return models_dir

    @classmethod
    def _synthesize_piper_local(cls, text: str, language: str = "en") -> Optional[Dict[str, Any]]:
        """
        Local neural TTS synthesis via Piper. Completely offline, zero-cost.
        """
        if not HAS_PIPER or piper is None:
            return None

        try:
            models_dir = cls._get_models_storage_path()
            onnx_path = os.path.join(models_dir, "en_US-lessac-medium.onnx")
            json_path = os.path.join(models_dir, "en_US-lessac-medium.onnx.json")

            # Download lightweight standard model on first run if not present
            if not os.path.exists(onnx_path) or not os.path.exists(json_path):
                import urllib.request
                logger.info("[TTSService] Downloading lightweight Piper neural voice model (en_US-lessac-medium)...")
                onnx_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
                json_url = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
                try:
                    urllib.request.urlretrieve(onnx_url, onnx_path)
                    urllib.request.urlretrieve(json_url, json_path)
                    logger.info("[TTSService] Piper voice model downloaded successfully.")
                except Exception as dl_err:
                    logger.warning(f"[TTSService] Could not download Piper model: {dl_err}")
                    return None

            if os.path.exists(onnx_path) and os.path.exists(json_path):
                if cls._piper_voice is None or cls._piper_model_path != onnx_path:
                    if hasattr(piper, "PiperVoice") and hasattr(piper.PiperVoice, "load"):
                        cls._piper_voice = piper.PiperVoice.load(onnx_path, config_path=json_path)
                    elif PiperVoice and hasattr(PiperVoice, "load"):
                        cls._piper_voice = PiperVoice.load(onnx_path, config_path=json_path)
                    cls._piper_model_path = onnx_path

                if cls._piper_voice:
                    audio_id = str(uuid.uuid4())
                    filename = f"{audio_id}.wav"
                    media_folder = cls._get_media_storage_path()
                    out_path = os.path.join(media_folder, filename)

                    with wave.open(out_path, "wb") as wav_file:
                        if hasattr(cls._piper_voice, "synthesize_wav"):
                            getattr(cls._piper_voice, "synthesize_wav")(text, wav_file)
                        else:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(2)
                            sample_rate = getattr(cls._piper_voice.config, "sample_rate", 22050)
                            wav_file.setframerate(sample_rate)
                            chunks = getattr(cls._piper_voice, "synthesize")(text)
                            for chunk in chunks:
                                audio_bytes = getattr(chunk, "audio_int16_bytes", None)
                                if audio_bytes:
                                    wav_file.writeframes(audio_bytes)

                    # Compute duration from WAV header
                    with wave.open(out_path, "rb") as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        duration = max(2.0, round(frames / float(rate), 2))

                    logger.info(f"[TTSService] Synthesized local Piper audio: {filename} ({duration}s)")
                    return {
                        "provider": "piper_local",
                        "success": True,
                        "audio_url": f"/media/{filename}",
                        "duration_seconds": duration,
                        "language": language,
                        "voice_id": "piper-en_US-lessac-medium"
                    }
        except Exception as piper_err:
            logger.warning(f"[TTSService] Local Piper TTS synthesis error: {piper_err}")
        return None

    @classmethod
    async def synthesize_speech(
        cls, 
        text: str, 
        language: str = "en", 
        voice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Hierarchical Speech Synthesis Pipeline:
        1. ElevenLabs API (if key configured and valid)
        2. Local Piper TTS (free, offline neural synthesis)
        3. Browser Web Speech API metadata fallback
        """
        voice = voice_id or settings.ELEVENLABS_DEFAULT_VOICE_ID or "21m00Tcm4TlvDq8ikWAM"
        
        # 1. Try ElevenLabs API
        if settings.ELEVENLABS_API_KEY and len(settings.ELEVENLABS_API_KEY.strip()) > 10:
            try:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        url,
                        headers={
                            "xi-api-key": settings.ELEVENLABS_API_KEY,
                            "Content-Type": "application/json"
                        },
                        json={
                            "text": text,
                            "model_id": "eleven_multilingual_v2",
                            "voice_settings": {
                                "stability": 0.5,
                                "similarity_boost": 0.75
                            }
                        }
                    )
                    if resp.status_code == 200 and resp.content:
                        audio_id = str(uuid.uuid4())
                        filename = f"{audio_id}.mp3"
                        media_folder = cls._get_media_storage_path()
                        file_path = os.path.join(media_folder, filename)
                        
                        with open(file_path, "wb") as f:
                            f.write(resp.content)

                        # Approximate duration (128kbps ~ 16KB/s)
                        est_duration = max(3.0, round(len(resp.content) / 16000, 2))
                        
                        logger.info(f"[TTSService] Generated ElevenLabs audio file: {filename} ({len(resp.content)} bytes)")
                        return {
                            "provider": "elevenlabs",
                            "success": True,
                            "audio_url": f"/media/{filename}",
                            "duration_seconds": est_duration,
                            "language": language,
                            "voice_id": voice
                        }
                    else:
                        logger.warning(f"[TTSService] ElevenLabs API status {resp.status_code}: {resp.text[:150]}")
            except Exception as e:
                logger.warning(f"[TTSService] ElevenLabs synthesis failed: {e}")

        # 2. Try Local Piper TTS
        piper_result = cls._synthesize_piper_local(text, language=language)
        if piper_result and piper_result.get("audio_url"):
            return piper_result

        # 3. Browser Web Speech fallback
        words = len(text.split())
        est_words_duration = max(4.0, round(words / 2.2, 2))
        voice_map = {
            "hi": "Google Speech Hindi",
            "ta": "Google தமிழ்",
            "te": "Google తెలుగు",
            "bn": "Google বাংলা",
            "es": "Google español",
        }
        return {
            "provider": "browser_speech_synthesis",
            "success": True,
            "audio_url": None,
            "duration_seconds": est_words_duration,
            "language": language,
            "voice_name": voice_map.get(language, "Google Speech English"),
            "text": text
        }

    @classmethod
    async def generate_speech(cls, text: str, language: str = "en", voice_id: Optional[str] = None) -> Dict[str, Any]:
        return await cls.synthesize_speech(text, language, voice_id)
