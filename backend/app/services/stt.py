import httpx
from typing import Optional
from ..config import settings

class STTService:
    @classmethod
    async def transcribe_audio(
        cls, 
        audio_bytes: bytes, 
        content_type: str = "audio/wav",
        language: str = "en"
    ) -> str:
        """
        Transcribes speech using Deepgram Nova-2 API with high accuracy and low latency.
        Supports regional language detection and explicit language hint (ta, hi, en, etc.).
        """
        if not settings.DEEPGRAM_API_KEY or len(settings.DEEPGRAM_API_KEY.strip()) < 5:
            return ""

        deepgram_lang = language if language in ["en", "hi", "ta", "te", "bn", "es"] else "en"
        url = f"https://api.deepgram.com/v1/listen?model={settings.DEEPGRAM_MODEL}&smart_format=true&language={deepgram_lang}"
        headers = {
            "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
            "Content-Type": content_type
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, content=audio_bytes)
                if response.status_code == 200:
                    data = response.json()
                    channels = data.get("results", {}).get("channels", [])
                    if channels:
                        alts = channels[0].get("alternatives", [])
                        if alts:
                            return alts[0].get("transcript", "")
                else:
                    print(f"[STTService] Deepgram API returned status {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[STTService] Deepgram transcription error: {e}")

        return ""
