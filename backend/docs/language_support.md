# Regional Language Support & Tuning Template

Sahayak AI Teacher is built to deliver culturally rooted, intuitive education across multilingual India and globally. This document details the architectural template used to expand and tune regional language support.

Currently tuned languages:
- **English (`en`)**: Native baseline
- **Hindi (`hi`)**: Devanagari script with English domain technical term preservation
- **Hinglish (`hinglish`)**: Conversational Latin script with English terminology
- **Tamil (`ta`)**: Tamil script with English domain technical terminology and culturally relatable pedagogical examples

---

## 1. The Language Expansion Pattern

To add or deepen a new language (e.g., Telugu `te`, Bengali `bn`, Marathi `mr`, Kannada `kn`), follow these 5 synchronized layers:

### Layer 1: Lesson Planning System Prompt Clause (`app/state_machine/teacher_agent.py`)

In `TeacherAgentStateMachine.generate_lesson_plan`, define the system instruction language rule:

```python
lang_clause = f"Language: {effective_lang}."
if effective_lang == "ta":
    lang_clause += (
        " Explain in natural, conversational Tamil (Tamil script) while strictly preserving "
        "domain technical terminology in English (or bilingual Tamil+English). Provide intuitive real-world analogies."
    )
```

**Rule of Thumb**: Always instruct the model to preserve core STEM and technical terminology in English (e.g., *Binary Search*, *Potential Energy*, *Mitochondria*, *Gradient Descent*). Indian students learn technical definitions in English even in regional medium classrooms.

### Layer 2: Segment Delivery & Socratic Pedagogy Guide (`app/state_machine/teacher_agent.py`)

In `TeacherAgentStateMachine.render_segment`, inject the explicit language hybrid rule into `pedagogy_guide`:

```python
elif active_lang == "ta":
    pedagogy_guide += (
        "CRITICAL TAMIL HYBRID TEACHING RULE: Write clear, engaging, conversational explanations in Tamil (Tamil script), "
        "while strictly preserving domain technical terminology in English (e.g., 'Kinetic Energy', 'Binary Search', 'Algorithm', 'Photosynthesis', 'Momentum', 'Derivative'). "
        "Use simple everyday relatable analogies and formulate checkpoint questions clearly in Tamil."
    )
```

### Layer 3: Template Fallbacks for Spoken Script & Blackboard (`app/state_machine/teacher_agent.py`)

Always provide a culturally coherent fallback script and on-screen blackboard summary in the regional language in case external LLM APIs fail:

```python
elif active_lang == "ta":
    spoken_script = (
        f"வணக்கம்! இன்று நாம் {concept} பற்றி எளிமையாகவும் தெளிவாகவும் கற்றுக்கொள்ளப் போகிறோம். "
        f"இது அறிவியலிலும் நடைமுறை உலகிலும் மிக முக்கியமான ஒரு கருத்தாகும்.{obs_guide} திரையில் தோன்றும் விளக்கப் படத்தை உற்று கவனியுங்கள்."
    )
    on_screen_text = (
        f"📚 தலைப்பு: {concept}\n\n"
        f"• {v_decision.pedagogical_goal or 'அடிப்படைக் கருத்து விளக்கம்'}\n"
        "• முதன்மை சூத்திரங்கள் மற்றும் சமன்பாடுகள்\n"
        "• நடைமுறை பயன்பாடுகள்"
    )
```

### Layer 4: Voice & Speech Engine Mappings (`app/services/tts.py` & `app/services/stt.py`)

- **Text-to-Speech (TTS)**:
  - ElevenLabs supports multilingual synthesis via the `eleven_multilingual_v2` model.
  - In Web Speech fallback, map the language code to the system regional voice name in `voice_map`:
    ```python
    voice_map = {
        "hi": "Google Speech Hindi",
        "ta": "Google தமிழ்",
        "te": "Google తెలుగు",
        "bn": "Google বাংলা",
        "es": "Google español",
    }
    ```
- **Speech-to-Text (STT)**:
  - Deepgram Nova-2 accepts language codes: pass `&language=ta`, `&language=hi`, `&language=te`, etc. to enable localized acoustic models.

### Layer 5: Visual Search & Video Grounding (`app/services/youtube.py`)

Configure locale and script hints so YouTube queries return high-quality educational videos in the intended regional language:

```python
elif lang == "ta":
    q = f"{q} தமிழ்"  # Tamil script hint biases results to regional educator channels
    params = {"search_query": q, "hl": "ta", "gl": "IN"}
```

---

## 2. Verification Checklist for New Languages

When adding a language:
1. [ ] Update `SUPPORTED_LANGUAGES` in `app/config.py`.
2. [ ] Add planning prompt clause in `teacher_agent.py`.
3. [ ] Add segment rendering pedagogical guide in `teacher_agent.py`.
4. [ ] Add spoken script and blackboard on-screen text template in `teacher_agent.py`.
5. [ ] Verify Web Speech voice mapping in `tts.py`.
6. [ ] Verify STT language parameter in `stt.py`.
7. [ ] Verify YouTube search localization in `youtube.py`.
8. [ ] Perform end-to-end test generation: check that technical terms remain in English and grammar flows naturally in the regional script.
