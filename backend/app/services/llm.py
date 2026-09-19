import json
import re
import logging
import httpx
from typing import Dict, Any, Optional, List, Union
from ..config import settings

logger = logging.getLogger("sahayak.llm")

class LLMUnavailable(Exception):
    """Raised when no LLM provider is configured, all fail, or response is unparseable."""
    pass

class LLMService:
    @classmethod
    async def _call_gemini(cls, system_prompt: str, user_prompt: str, temperature: float) -> str:
        if not settings.GEMINI_API_KEY or len(settings.GEMINI_API_KEY.strip()) < 5:
            return ""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 4096
            }
        }
        if system_prompt:
            payload["systemInstruction"] = {
                "parts": [{"text": system_prompt}]
            }
            
        async with httpx.AsyncClient(timeout=35.0) as client:
            resp = await client.post(
                endpoint,
                headers={"Content-Type": "application/json"},
                json=payload
            )
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return parts[0]["text"].strip()
            else:
                logger.warning(f"[LLMService] Gemini API failed with status {resp.status_code}: {resp.text}")
        return ""

    @classmethod
    async def _call_groq(cls, system_prompt: str, user_prompt: str, temperature: float) -> str:
        if not settings.GROQ_API_KEY or len(settings.GROQ_API_KEY.strip()) < 5:
            return ""
        async with httpx.AsyncClient(timeout=35.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.GROQ_MODEL,
                    "max_tokens": 4096,
                    "temperature": temperature,
                    "messages": [
                        {"role": "system", "content": system_prompt or "You are an expert AI teacher."},
                        {"role": "user", "content": user_prompt}
                    ]
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "").strip()
            else:
                logger.warning(f"[LLMService] Groq API failed with status {resp.status_code}: {resp.text}")
        return ""

    @classmethod
    async def _call_anthropic(cls, system_prompt: str, user_prompt: str, temperature: float) -> str:
        if not settings.ANTHROPIC_API_KEY or len(settings.ANTHROPIC_API_KEY.strip()) < 5:
            return ""
        async with httpx.AsyncClient(timeout=35.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": settings.ANTHROPIC_MODEL,
                    "max_tokens": 4096,
                    "temperature": temperature,
                    "system": system_prompt or "You are an expert AI teacher.",
                    "messages": [{"role": "user", "content": user_prompt}]
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content", [])
                if content and "text" in content[0]:
                    return content[0]["text"].strip()
            else:
                logger.warning(f"[LLMService] Anthropic API failed with status {resp.status_code}: {resp.text}")
        return ""

    @classmethod
    async def generate_response(
        cls, 
        system_prompt: str, 
        user_prompt: str, 
        temperature: float = 0.2
    ) -> str:
        """
        Executes an LLM call according to LLM_PROVIDER_ORDER setting.
        Raises LLMUnavailable if all providers fail or are unconfigured.
        """
        provider_order = [p.strip().lower() for p in settings.LLM_PROVIDER_ORDER.split(",") if p.strip()]
        if not provider_order:
            provider_order = ["gemini", "groq", "anthropic"]

        for provider in provider_order:
            try:
                if provider == "gemini":
                    text = await cls._call_gemini(system_prompt, user_prompt, temperature)
                elif provider == "groq":
                    text = await cls._call_groq(system_prompt, user_prompt, temperature)
                elif provider == "anthropic":
                    text = await cls._call_anthropic(system_prompt, user_prompt, temperature)
                else:
                    logger.warning(f"[LLMService] Unknown provider: {provider}")
                    continue

                if text and len(text.strip()) > 0:
                    return text
            except Exception as e:
                logger.warning(f"[LLMService] Provider '{provider}' invocation error: {e}")

        raise LLMUnavailable("No active LLM provider returned a valid response.")

    @classmethod
    async def stream_response(
        cls, 
        system_prompt: str, 
        user_prompt: str, 
        temperature: float = 0.2
    ):
        """
        Async generator yielding text deltas incrementally from Gemini (SSE) or Groq (stream: true).
        Falls back to yielding full generate_response once on failure.
        """
        provider_order = [p.strip().lower() for p in settings.LLM_PROVIDER_ORDER.split(",") if p.strip()]
        if not provider_order:
            provider_order = ["gemini", "groq", "anthropic"]

        for provider in provider_order:
            if provider == "gemini" and settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
                try:
                    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:streamGenerateContent?alt=sse&key={settings.GEMINI_API_KEY}"
                    payload: Dict[str, Any] = {
                        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                        "generationConfig": {"temperature": temperature, "maxOutputTokens": 4096}
                    }
                    if system_prompt:
                        payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

                    async with httpx.AsyncClient(timeout=45.0) as client:
                        async with client.stream("POST", endpoint, json=payload) as response:
                            if response.status_code == 200:
                                streamed_any = False
                                async for line in response.aiter_lines():
                                    line = line.strip()
                                    if line.startswith("data:"):
                                        data_str = line[5:].strip()
                                        if not data_str:
                                            continue
                                        try:
                                            data = json.loads(data_str)
                                            candidates = data.get("candidates", [])
                                            if candidates and "content" in candidates[0]:
                                                parts = candidates[0]["content"].get("parts", [])
                                                for p in parts:
                                                    txt = p.get("text", "")
                                                    if txt:
                                                        streamed_any = True
                                                        yield txt
                                        except Exception:
                                            continue
                                if streamed_any:
                                    return
                except Exception as e:
                    logger.warning(f"[LLMService] Gemini streaming error: {e}")

            elif provider == "groq" and settings.GROQ_API_KEY and len(settings.GROQ_API_KEY.strip()) > 5:
                try:
                    async with httpx.AsyncClient(timeout=45.0) as client:
                        async with client.stream(
                            "POST",
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={
                                "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": settings.GROQ_MODEL,
                                "max_tokens": 4096,
                                "temperature": temperature,
                                "stream": True,
                                "messages": [
                                    {"role": "system", "content": system_prompt or "You are an expert AI teacher."},
                                    {"role": "user", "content": user_prompt}
                                ]
                            }
                        ) as response:
                            if response.status_code == 200:
                                streamed_any = False
                                async for line in response.aiter_lines():
                                    line = line.strip()
                                    if line.startswith("data:"):
                                        data_str = line[5:].strip()
                                        if data_str == "[DONE]":
                                            break
                                        try:
                                            data = json.loads(data_str)
                                            choices = data.get("choices", [])
                                            if choices:
                                                delta = choices[0].get("delta", {})
                                                content = delta.get("content", "")
                                                if content:
                                                    streamed_any = True
                                                    yield content
                                        except Exception:
                                            continue
                                if streamed_any:
                                    return
                except Exception as e:
                    logger.warning(f"[LLMService] Groq streaming error: {e}")

        # Fallback to single-shot generate_response
        try:
            full_text = await cls.generate_response(system_prompt, user_prompt, temperature)
            yield full_text
        except Exception as e:
            logger.warning(f"[LLMService] Fallback streaming generation failed: {e}")
            yield "Welcome! Let us explore this fundamental educational concept from first principles."

    @classmethod
    def _strip_markdown_json(cls, raw: str) -> str:
        """Strips markdown code blocks, backticks, and extra whitespace to isolate JSON."""
        cleaned = raw.strip()
        # Match ```json ... ``` or ``` ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if fence_match:
            cleaned = fence_match.group(1).strip()
        # Find first { or [ and last } or ]
        first_brace = cleaned.find("{")
        first_bracket = cleaned.find("[")
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            last_brace = cleaned.rfind("}")
            if last_brace != -1:
                cleaned = cleaned[first_brace:last_brace+1]
        elif first_bracket != -1:
            last_bracket = cleaned.rfind("]")
            if last_bracket != -1:
                cleaned = cleaned[first_bracket:last_bracket+1]
        return cleaned

    @classmethod
    async def generate_json(
        cls,
        system_prompt: str,
        user_prompt: str,
        schema_hint: Optional[Union[str, Dict[str, Any]]] = None,
        response_schema: Optional[Union[str, Dict[str, Any]]] = None,
        temperature: float = 0.2,
        **kwargs: Any
    ) -> Any:
        """
        Calls generate_response(), strips markdown code fences, parses JSON,
        and on parse failure retries once with strict formatting enforcement.
        Raises LLMUnavailable on unrecoverable failure.
        """
        system_instruction = (system_prompt or "") + "\nCRITICAL: You must output ONLY valid RFC8259 JSON. No markdown fences, no explanatory text, no HTML."
        effective_schema = schema_hint if schema_hint is not None else response_schema
        if effective_schema:
            schema_str = json.dumps(effective_schema) if isinstance(effective_schema, dict) else str(effective_schema)
            system_instruction += f"\nJSON Schema Expected:\n{schema_str}"

        raw_output = ""
        try:
            raw_output = await cls.generate_response(system_instruction, user_prompt, temperature)
            cleaned = cls._strip_markdown_json(raw_output)
            return json.loads(cleaned)
        except json.JSONDecodeError as err:
            logger.warning(f"[LLMService] JSON parse failed on initial attempt: {err}. Retrying with strict formatting prompt.")
            retry_prompt = f"{user_prompt}\n\nCRITICAL FIX REQUIRED: Your previous response was not valid JSON:\n{raw_output[:500]}\nRespond with ONLY valid minified JSON adhering to the schema, starting with {{ or [."
            try:
                raw_retry = await cls.generate_response(system_instruction, retry_prompt, temperature=0.1)
                cleaned_retry = cls._strip_markdown_json(raw_retry)
                return json.loads(cleaned_retry)
            except Exception as retry_err:
                logger.error(f"[LLMService] JSON parse failed after retry: {retry_err}")
                raise LLMUnavailable(f"Failed to generate parseable JSON: {retry_err}")
        except Exception as e:
            raise LLMUnavailable(str(e))
