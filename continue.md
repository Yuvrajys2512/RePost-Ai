# Session Continuity — RePost AI

Read this at the start of every new session before touching any code.

---

## What Was Built This Session

### The AI pipeline is now real (partially)

The core problem was that every generator was a deterministic string template — no LLM
calls anywhere. We fixed that for the two most important generators.

**Files changed:**
- `backend/app/agents/llm.py` — NEW. Shared LLM caller. Picks provider automatically:
  Claude → Groq → Gemini → raises error. All generators import from here.
- `backend/app/agents/nodes/analyzer.py` — Replaced deterministic stub with real LLM call.
  Supports Claude (tool use / structured JSON), Groq (JSON mode), Gemini (JSON mode).
  Falls back to deterministic if no key is set (keeps tests green).
- `backend/app/agents/nodes/generators/twitter.py` — Replaced template with real LLM call.
  Writes AS the creator (first person), 5 distinct tweets, natural thread format.
  Falls back to deterministic if no LLM configured.
- `backend/app/agents/nodes/generators/linkedin.py` — Replaced template with real LLM call.
  First person, two different angles, proper LinkedIn format (hook / body / CTA).
  Falls back to deterministic if no LLM configured.
- `backend/app/config.py` — Added `groq_api_key` and `google_api_key` fields.
- `backend/app/main.py` — Added startup log showing which AI provider is active.
- `backend/app/services/jobs.py` — Fixed circular import (lazy import of graph.py).
- `backend/app/services/transcript.py` — Fixed youtube-transcript-api v1.x API change
  (`get_transcript` → `YouTubeTranscriptApi().fetch()`).
- `backend/pyproject.toml` — Added `anthropic`, `groq`, `google-genai` dependencies.
- `.env.example` — Added `GROQ_API_KEY` and `GOOGLE_API_KEY` with comments.
- `monetization.md` — NEW. Full ordered build guide with `[YOU]`/`[CODE]`/`[TEST]` flags.

**AI provider in use:** Groq (free, 14K req/day, Llama 3.3 70B).
Key is in `backend/.env` as `GROQ_API_KEY`. Do not commit `.env`.

**Quality test result:** Ran the pipeline against a real YouTube video (music/silence/creativity).
- Analyzer: 8/10 — hook, key ideas, quotes all specific to the video
- Twitter standalone: 8/10 — 5 distinct tweets, first person, no duplicates
- Twitter thread: 7/10 — content solid, verify numbering is CLI display not tweet text
- LinkedIn: 8/10 — first person, two different angles, specific CTAs

---

## Exact Next Step — Resume Here

**We are in Block 1 of `monetization.md`.**

The Twitter and LinkedIn generators are done. The remaining 4 generators still use
deterministic templates and need real LLM calls, following the exact same pattern.

### Task: Replace the remaining 4 generators with real LLM calls

Work through these in order. Each one follows the same pattern as twitter.py and linkedin.py:
1. Read the current generator file
2. Write a platform-specific system prompt (the creative brief for that platform)
3. Write a `_build_user_message()` function that formats the ContentAnalysis
4. Call `call_llm_json()` from `app.agents.llm`
5. Parse the JSON into the existing schema
6. Keep deterministic as fallback

**Files to rewrite (in this order):**

```
backend/app/agents/nodes/generators/newsletter.py
backend/app/agents/nodes/generators/blog.py
backend/app/agents/nodes/generators/shorts.py
backend/app/agents/nodes/generators/carousel.py
```

**Schemas to match** (read `backend/app/schemas/generation.py`):
- `NewsletterContent`: subject_lines (3-5), preview_text, body, cta
- `BlogContent`: title, meta_description, introduction, sections (min 3 BlogSection), conclusion
  - `BlogSection`: heading, body
- `ShortsContent`: clips (3-5 ShortsClip)
  - `ShortsClip`: title, start_seconds, end_seconds, hook, script
- `CarouselContent`: title, slides (6-10 CarouselSlide), caption
  - `CarouselSlide`: slide_number, headline, body

**Platform-specific prompt guidance** (from system-design.md):
- Newsletter: 3 subject line options, curiosity-gap subject lines under 50 chars,
  personal hook opener (NOT "In this video I..."), 3-4 key insights as paragraphs, CTA to video
- Blog: SEO title, meta description, proper H2 sections from key ideas, 800-1500 words
- Shorts: 3-5 clip suggestions with real timestamps (use video duration from transcript),
  each clip under 60 seconds, hook + script outline for each
- Carousel: 6-10 slides, slide 1 is hook/promise, slides 2-N are insights, last slide is CTA

### After all generators are done:

**Build the QA node** (`backend/app/agents/nodes/qa.py`).
The QA node reviews every generated piece and checks:
- Generic language ("Let's dive in", "game-changer", "In today's world") → retry
- Tweets over 280 chars → reformat
- LinkedIn body under 25 words → retry
- Factual claims not in the transcript → correct or remove
Max 1 retry cycle per piece, then pass with a warning flag.

### Then: [YOU] task
Test the full pipeline against 10 real YouTube videos across different niches.
Score each output 1-10. Target average ≥ 7. Note which generator fails most often.

---

## Provider Setup

```
Priority: Claude (paid, best) → Groq (free, current) → Gemini (free, limited)
```

Groq key is in `backend/.env`. If hitting rate limits, user needs to either:
- Wait until next day (14K/day limit resets)
- Get a new Groq project key at console.groq.com

Gemini key also in `.env` but user's Google account quota is exhausted across projects.
Do not switch to Gemini unless Groq also fails.

When ready for production: add `ANTHROPIC_API_KEY` to `.env` and Claude takes over
automatically — no code changes needed.

---

## Running the Pipeline

```powershell
# From backend/ with venv active
cd backend
.\.venv\Scripts\Activate.ps1
python -m app.agents.cli "https://www.youtube.com/watch?v=VIDEO_ID"

# To see raw JSON output
python -m app.agents.cli "https://www.youtube.com/watch?v=VIDEO_ID" --json
```

## Known Issues / Things to Check Next Session

1. **Twitter thread numbering** — the CLI output showed "1. 2. 3." prefix on thread tweets.
   Need to verify if this is CLI display formatting or if the model is actually adding numbers
   to the tweet text. Run with `--json` flag and inspect the raw `thread` array.
   If tweet text starts with "1.", tighten the no-numbering rule in the Twitter system prompt.

2. **YouTube transcript API** — fixed for v1.2.4. If the library upgrades again and breaks,
   the fix is in `backend/app/services/transcript.py` line 30.

3. **Circular import** — was caused by `services/jobs.py` importing `graph.py` at module level.
   Fixed with lazy imports inside the two functions that need it. Do not move those imports
   back to the module top level.
