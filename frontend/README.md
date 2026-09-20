# Sahayak AI Teacher — Frontend 🎓

Modern, immersive educational web application built with **Next.js 15 (App Router)** and **React 19**, delivering an interactive theater-mode classroom, real-time blackboard visualization, audio-reactive animated canvas avatar, curriculum DAG exploration, and 8 advanced study tools for students.

---

## 🚀 Tech Stack

* **Framework**: [Next.js 15](https://nextjs.org/) (App Router, Server Components & Client Components)
* **UI Library**: [React 19](https://react.dev/)
* **Styling**: [TailwindCSS 3](https://tailwindcss.com/) + [DaisyUI 4](https://daisyui.com/)
* **Animations**: [Framer Motion 12](https://www.framer.com/motion/)
* **Data Visualization**: [Recharts](https://recharts.org/)
* **Mathematics & Equations**: [KaTeX](https://katex.org/)
* **Icons**: [Lucide React](https://lucide.dev/)
* **Celebrations**: Canvas Confetti

---

## 🗺️ Application Route Map

| Route | Purpose | Key Components |
|---|---|---|
| `/` | Landing page highlighting pedagogical value proposition, interactive previews, and call-to-actions | Hero banner, feature showcases, architecture walkthrough |
| `/login` | Authentication portal: student & teacher sign-in, account creation, and role selection | `AuthContext`, role selector, proficiency initializers |
| `/dashboard` | Learning Hub featuring 8 integrated study tools and student momentum analytics | Personalities, Revision, Flashcards, Notes, Homework, Exam Prep, Planner |
| `/upload` | Drag-and-drop ingestion for PDF, DOCX, PPTX, TXT, and Markdown educational materials | File dropzone, upload progress indicator, RAG extraction preview |
| `/topic` | Topic-based curriculum planner with custom natural-language instructions | Instruction parser, time-budget slider, depth controller |
| `/lesson/[id]` | Full Theater-Mode Classroom with synchronous video, blackboard, and checkpoints | `TeacherPlayer`, `AudioReactiveAvatar`, `VisualRenderer`, `CitationChip` |
| `/assessment/[id]` | Adaptive Bloom's taxonomy assessments with instant rubric-based grading | MCQ selector, open-ended response editor, voice answer recorder |
| `/report/[id]` | Diagnostic learning gap map pinpointing strengths, weaknesses, and citations | Gap map visualizer, remedial recommendation cards |
| `/profile` | Persistent student profile displaying concept mastery and learning history | Mastery progression bar, historical session tracker |
| `/learning-path` | Interactive directed acyclic graph (DAG) representing curriculum prerequisites | `LearningPathDAG`, node status badges (Mastered, In-Progress, Locked) |
| `/setup` | Onboarding questionnaire configuring learning style, pace, and language preference | Modality preference toggles, language selector |

---

## 🧩 Core Components Architecture

### 1. Theater Player (`src/components/TeacherPlayer.tsx`)
- **16:9 Cinema Stage**: Synchronous playback of generated explainer videos or interactive slide animations with Ken Burns pan-and-zoom motion.
- **Synchronized Captions**: Formatted subtitles burned-in or rendered with timing cues.
- **Interactive Blackboard**: Dynamically switches between KaTeX math equations, coordinate Cartesian graphs, biology SVG diagrams, and runnable Python code execution.
- **Voice STT Input**: Direct microphone capture via Deepgram Nova-2 for hands-free student responses.

### 2. Audio-Reactive Avatar (`src/components/AudioReactiveAvatar.tsx`)
- **Zero-Cost Web Audio Engine**: Connects an HTML5 Canvas to a Web Audio API `AnalyserNode`.
- **Mouth Articulation & Blinking**: Smooth mouth movement mapped to speech frequency amplitudes with random lifelike eye blinks.
- **Live Sound Wave Equalizer**: Ambient frequency equalizer bar visualizations pulsing in sync with voice narration.

### 3. Domain Visual Renderer (`src/components/VisualRenderer.tsx`)
- **Mathematics**: Instant rendering of LaTeX formulas via KaTeX with variable highlighting.
- **Science & Data**: Parametric 2D graphs rendered with Recharts.
- **Computer Science**: Integrated Python 3 code execution sandbox displaying live stdout, stderr, and isolated execution indicators.
- **Diagrams & Timelines**: High-resolution vector SVGs for anatomical, cellular, and historical progressions.

### 4. Learning Path DAG (`src/components/LearningPathDAG.tsx`)
- Visualizes prerequisite relationships between curriculum concepts.
- Nodes reflect mastery state: `Mastered` (emerald), `In-Progress` (blue), `Struggling` (amber), `Locked` (slate).
- Supports 1-click resumption of unfinished or weak topics.

### 5. Verified Citation Chips (`src/components/CitationChip.tsx`)
- Coursera-style interactive citation chips embedded directly inside lesson segments.
- Clicking displays source document name, page number, chunk ID, verbatim excerpt, and grounding confidence rating.

---

## 🔐 State Management & Contexts

* **`AuthContext` (`src/context/AuthContext.tsx`)**:
  - Manages JWT access tokens in localStorage and HTTP-only cookies.
  - Automatically loads and refreshes the current user profile from `/api/auth/me`.
  - Exposes `user`, `isAuthenticated`, `role` (`student` | `teacher`), `login()`, `register()`, and `logout()`.
* **`ToastContext` (`src/context/ToastContext.tsx`)**:
  - Global, non-blocking toast notifications for system alerts, network errors, and action confirmations.

---

## 🛠️ Local Development

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment Variables
Create `.env.local` in the `frontend` folder:
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api
```

### 3. Start Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Build for Production
```bash
npm run build
npm run start
```

---

## 🐳 Docker Deployment

The frontend includes an optimized multi-stage `Dockerfile`:
```bash
# Build standalone container
docker build -t sahayak-frontend .

# Run container
docker run -p 3000:3000 -e NEXT_PUBLIC_API_BASE_URL="/api" sahayak-frontend
```
When running with `docker-compose up`, the frontend is automatically networked to the backend service.
