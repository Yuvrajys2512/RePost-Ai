# RepostAI — System Design Document
## AI Content Repurposing Agent for YouTube Creators

---

## Table of Contents
1. Product Overview
2. High-Level Design (HLD)
3. Low-Level Design (LLD)
4. Database Schema
5. API Contract
6. Agent Pipeline (LangGraph) — Deep Dive
7. Phased Roadmap

---

## 1. Product Overview

### What It Does
A creator pastes a YouTube video URL → the system extracts the transcript → an agentic AI pipeline analyzes the content for key ideas, hooks, emotional beats, and narrative structure → platform-specific agents generate ready-to-publish content for Twitter/X, LinkedIn, newsletters, blogs, Instagram carousels, and YouTube Shorts scripts.

### Core Differentiator
Not generic AI summaries. The system understands *storytelling structure* — it identifies the hook, the tension, the insight, the payoff — and translates that structure into each platform's native format. Optionally learns the creator's voice from past content samples.

### Target User
US/UK/Canada YouTube creators with 1K-500K subscribers who publish 1-4 videos/week and want to maximize reach without hiring a content team.

### Revenue Model
- **Starter:** $19/month — 10 videos/month, Twitter + LinkedIn + Blog
- **Pro:** $29/month — 30 videos/month, all platforms + voice matching + Shorts timestamps
- **Agency:** $49/month — unlimited videos, multiple voice profiles, team seats, API access

---

## 2. High-Level Design (HLD)

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                         │
│                                                             │
│   ┌──────────────┐    ┌──────────────┐   ┌──────────────┐  │
│   │  Web App      │    │  Landing Page │   │  Dashboard   │  │
│   │  (React/Next) │    │  (Static)     │   │  (Analytics) │  │
│   └──────┬───────┘    └──────────────┘   └──────┬───────┘  │
│          │                                       │          │
└──────────┼───────────────────────────────────────┼──────────┘
           │                                       │
           ▼                                       ▼
┌─────────────────────────────────────────────────────────────┐
│                        API LAYER                            │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              FastAPI Application                     │   │
│   │                                                      │   │
│   │   /api/videos/process    POST  (submit URL)          │   │
│   │   /api/videos/{id}       GET   (status + results)    │   │
│   │   /api/content/{id}      GET   (individual piece)    │   │
│   │   /api/voice-profile     POST  (upload voice samples)│   │
│   │   /api/history           GET   (past generations)    │   │
│   │   /api/auth/*            POST  (auth endpoints)      │   │
│   │   /api/billing/*         POST  (payment webhooks)    │   │
│   └────────────────────┬────────────────────────────────┘   │
│                        │                                     │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    PROCESSING LAYER                          │
│                                                             │
│   ┌─────────────┐    ┌──────────────────────────────────┐   │
│   │  Task Queue  │───▶│     LangGraph Agent Pipeline     │   │
│   │  (Redis +    │    │                                  │   │
│   │   Celery/    │    │  Transcript → Analyze → Route    │   │
│   │   ARQ)       │    │  → Generate → QA → Output        │   │
│   └─────────────┘    └──────────────┬───────────────────┘   │
│                                      │                       │
└──────────────────────────────────────┼───────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                             │
│                                                             │
│   ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│   │  PostgreSQL   │  │  Redis       │  │  Object Storage │  │
│   │  (Supabase)   │  │  (Cache +    │  │  (S3/Supabase   │  │
│   │               │  │   Queue)     │  │   Storage)      │  │
│   │  - users      │  │              │  │                 │  │
│   │  - videos     │  │  - job queue │  │  - voice samples│  │
│   │  - content    │  │  - rate limit│  │  - exports      │  │
│   │  - profiles   │  │  - cache     │  │                 │  │
│   └──────────────┘  └──────────────┘  └─────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                         │
│                                                             │
│   ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌────────────┐  │
│   │ YouTube  │ │ Anthropic│ │ Lemon      │ │ Supabase   │  │
│   │ Data API │ │ Claude   │ │ Squeezy    │ │ Auth       │  │
│   │          │ │ API      │ │ (Payments) │ │            │  │
│   └──────────┘ └──────────┘ └────────────┘ └────────────┘  │
│                                                             │
│   ┌──────────┐ ┌──────────┐                                 │
│   │ Resend   │ │ Sentry   │                                 │
│   │ (Email)  │ │ (Errors) │                                 │
│   └──────────┘ └──────────┘                                 │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow — Happy Path

```
Creator pastes YouTube URL
       │
       ▼
[1] API receives URL, validates it, checks user quota
       │
       ▼
[2] Creates a "job" record in DB (status: QUEUED)
       │
       ▼
[3] Pushes job to task queue, returns job_id to frontend
       │
       ▼
[4] Worker picks up job, triggers LangGraph pipeline
       │
       ├──▶ [4a] Extract transcript (youtube-transcript-api)
       │         If unavailable → fallback to yt-dlp + Whisper
       │
       ├──▶ [4b] Content Analyzer agent processes transcript
       │         Extracts: key ideas, hooks, quotes, structure,
       │         emotional beats, controversy, data points
       │
       ├──▶ [4c] Platform agents generate content in parallel
       │         Each agent has platform-specific system prompts
       │         Optional: voice profile injected for tone matching
       │
       ├──▶ [4d] QA agent reviews all output
       │         Checks for: generic language, factual consistency,
       │         platform format compliance, voice drift
       │
       └──▶ [4e] Results saved to DB (status: COMPLETED)
                  │
                  ▼
[5] Frontend polls for status → receives content kit
[6] Creator copies/edits/exports content
```

---

## 3. Low-Level Design (LLD)

### 3.1 Project Structure

```
repost-ai/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Environment config (pydantic-settings)
│   │   ├── dependencies.py         # Shared dependencies (DB, auth, etc.)
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── videos.py       # /api/videos/* endpoints
│   │   │   │   ├── content.py      # /api/content/* endpoints
│   │   │   │   ├── voice.py        # /api/voice-profile endpoints
│   │   │   │   ├── history.py      # /api/history endpoints
│   │   │   │   ├── auth.py         # /api/auth/* endpoints
│   │   │   │   └── billing.py      # /api/billing/* webhooks
│   │   │   └── middleware/
│   │   │       ├── auth.py         # JWT verification middleware
│   │   │       └── rate_limit.py   # Rate limiting middleware
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User SQLAlchemy model
│   │   │   ├── video.py            # Video/Job model
│   │   │   ├── content.py          # Generated content model
│   │   │   └── voice_profile.py    # Voice profile model
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── video.py            # Pydantic request/response schemas
│   │   │   ├── content.py
│   │   │   └── user.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── transcript.py       # YouTube transcript extraction
│   │   │   ├── quota.py            # Usage tracking & plan limits
│   │   │   └── export.py           # Export to markdown/PDF/notion
│   │   │
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── session.py          # DB session management
│   │       └── migrations/         # Alembic migrations
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── graph.py                # Main LangGraph definition
│   │   ├── state.py                # Shared agent state schema
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── transcript.py       # Transcript extraction node
│   │   │   ├── analyzer.py         # Content analysis node
│   │   │   ├── router.py           # Platform routing node
│   │   │   ├── generators/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── twitter.py      # Twitter/X content generator
│   │   │   │   ├── linkedin.py     # LinkedIn post generator
│   │   │   │   ├── newsletter.py   # Newsletter draft generator
│   │   │   │   ├── blog.py         # Blog post generator
│   │   │   │   ├── shorts.py       # YouTube Shorts script generator
│   │   │   │   └── carousel.py     # Instagram carousel generator
│   │   │   └── qa.py               # Quality assurance node
│   │   ├── prompts/
│   │   │   ├── analyzer.py         # Content analysis prompts
│   │   │   ├── twitter.py          # Platform-specific prompts
│   │   │   ├── linkedin.py
│   │   │   ├── newsletter.py
│   │   │   ├── blog.py
│   │   │   ├── shorts.py
│   │   │   ├── carousel.py
│   │   │   └── qa.py
│   │   └── tools/
│   │       ├── __init__.py
│   │       └── youtube.py          # YouTube data fetching tools
│   │
│   ├── workers/
│   │   ├── __init__.py
│   │   └── process_video.py        # Celery/ARQ task definition
│   │
│   ├── tests/
│   │   ├── test_transcript.py
│   │   ├── test_agents.py
│   │   ├── test_api.py
│   │   └── fixtures/
│   │       └── sample_transcripts.json
│   │
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx            # Landing / hero page
│   │   │   ├── dashboard/
│   │   │   │   ├── page.tsx        # Main dashboard
│   │   │   │   └── [videoId]/
│   │   │   │       └── page.tsx    # Content kit view
│   │   │   ├── settings/
│   │   │   │   └── page.tsx        # Voice profile, billing
│   │   │   └── auth/
│   │   │       ├── login/page.tsx
│   │   │       └── signup/page.tsx
│   │   ├── components/
│   │   │   ├── ui/                 # Shared UI primitives
│   │   │   ├── VideoInput.tsx      # URL input component
│   │   │   ├── ContentKit.tsx      # Generated content display
│   │   │   ├── PlatformTab.tsx     # Platform switcher tabs
│   │   │   ├── ContentCard.tsx     # Individual content piece
│   │   │   ├── ProcessingStatus.tsx# Real-time job status
│   │   │   └── VoiceProfileForm.tsx
│   │   ├── lib/
│   │   │   ├── api.ts              # API client
│   │   │   ├── auth.ts             # Auth helpers
│   │   │   └── utils.ts
│   │   └── hooks/
│   │       ├── usePolling.ts       # Poll job status
│   │       └── useContentKit.ts
│   ├── package.json
│   ├── tailwind.config.ts
│   └── next.config.ts
│
├── docker-compose.yml
├── README.md
└── .github/
    └── workflows/
        └── deploy.yml
```

### 3.2 LangGraph Agent Pipeline — Detailed Design

This is the brain of the product. Here's the exact graph structure:

```
                    ┌──────────────┐
                    │    START     │
                    └──────┬───────┘
                           │
                           ▼
                ┌────────────────────┐
                │  extract_transcript │
                │                    │
                │  Input: youtube_url│
                │  Output: raw text, │
                │  video metadata    │
                └────────┬───────────┘
                         │
                         ▼
                ┌────────────────────┐
                │  analyze_content   │
                │                    │
                │  Extracts:         │
                │  - core_thesis     │
                │  - key_ideas[]     │
                │  - hooks[]         │
                │  - quotable_lines[]│
                │  - emotional_beats│
                │  - data_points[]   │
                │  - narrative_arc   │
                │  - target_audience │
                │  - controversy     │
                └────────┬───────────┘
                         │
                         ▼
                ┌────────────────────┐
                │   route_platforms  │
                │                    │
                │  Based on user's   │
                │  plan + preferences│
                │  determines which  │
                │  generators to run │
                └────────┬───────────┘
                         │
            ┌────────────┼────────────────┐
            │            │                │
            ▼            ▼                ▼
    ┌──────────┐  ┌──────────┐    ┌──────────┐
    │ generate  │  │ generate  │    │ generate  │
    │ _twitter  │  │ _linkedin │    │ _newsletter│  ... (parallel)
    │           │  │           │    │           │
    │ 5-8 posts │  │ 2-3 posts │    │ 1 draft   │
    │ + thread  │  │           │    │           │
    └─────┬─────┘  └─────┬─────┘    └─────┬─────┘
          │              │                │
          └──────────────┼────────────────┘
                         │
                         ▼
                ┌────────────────────┐
                │  quality_check     │
                │                    │
                │  For each piece:   │
                │  - generic? → redo │
                │  - off-voice? fix  │
                │  - wrong format?   │
                │  - factually wrong?│
                └────────┬───────────┘
                         │
                         ▼
                ┌────────────────────┐
                │  compile_output    │
                │                    │
                │  Formats final kit │
                │  Saves to DB       │
                └────────┬───────────┘
                         │
                         ▼
                    ┌──────────┐
                    │   END    │
                    └──────────┘
```

### 3.3 Agent State Schema

```python
from typing import TypedDict, Literal
from pydantic import BaseModel

# --- Content Analysis Output ---

class KeyIdea(BaseModel):
    idea: str                          # The core idea in one sentence
    supporting_quote: str              # Exact quote from transcript
    timestamp_start: float | None      # Seconds into the video
    emotional_weight: str              # "surprising" | "controversial" | "inspiring" | "practical"

class ContentAnalysis(BaseModel):
    core_thesis: str                   # What is this video fundamentally about?
    key_ideas: list[KeyIdea]           # 3-8 key ideas, ranked by impact
    hooks: list[str]                   # Attention-grabbing opening lines found
    quotable_lines: list[str]          # Lines that stand alone as tweets/quotes
    data_points: list[str]             # Any numbers, stats, research cited
    narrative_arc: str                 # "problem-solution" | "story" | "listicle" | "debate" | "tutorial"
    target_audience: str               # Who is the creator speaking to?
    emotional_journey: list[str]       # Sequence of emotional beats
    controversy_level: str             # "none" | "mild" | "spicy" | "hot"

# --- Generated Content Pieces ---

class TwitterContent(BaseModel):
    standalone_tweets: list[str]       # 5-8 individual tweets
    thread: list[str]                  # A full thread (5-12 tweets)
    engagement_hooks: list[str]        # Quote-tweet worthy lines

class LinkedInContent(BaseModel):
    posts: list[str]                   # 2-3 LinkedIn posts (each 150-300 words)
    # LinkedIn format: hook line → story/insight → takeaway → CTA

class NewsletterContent(BaseModel):
    subject_lines: list[str]           # 3 subject line options
    body: str                          # Full newsletter draft
    # Format: intro hook → 3-4 key insights with commentary → CTA

class BlogContent(BaseModel):
    title: str
    meta_description: str              # SEO meta description
    outline: list[str]                 # H2 headers
    body: str                          # Full blog post (800-1500 words)
    seo_keywords: list[str]

class ShortsContent(BaseModel):
    clips: list[dict]                  # Each: { hook, timestamp_start, timestamp_end, script, caption }

class CarouselContent(BaseModel):
    slides: list[dict]                 # Each: { slide_number, headline, body, visual_suggestion }
    caption: str                       # Instagram caption

# --- LangGraph State ---

class PipelineState(TypedDict):
    # Input
    youtube_url: str
    user_id: str
    job_id: str
    target_platforms: list[str]        # ["twitter", "linkedin", "newsletter", ...]
    voice_profile: str | None          # Past content samples for voice matching

    # After transcript extraction
    transcript: str
    video_title: str
    video_description: str
    video_duration: int                # seconds
    channel_name: str

    # After analysis
    analysis: ContentAnalysis

    # After generation (each populated by its respective node)
    twitter: TwitterContent | None
    linkedin: LinkedInContent | None
    newsletter: NewsletterContent | None
    blog: BlogContent | None
    shorts: ShortsContent | None
    carousel: CarouselContent | None

    # After QA
    qa_passed: bool
    qa_feedback: list[str]             # Issues found by QA agent
    retry_count: int                   # Max 2 retries

    # Metadata
    status: str                        # "extracting" | "analyzing" | "generating" | "reviewing" | "done" | "failed"
    error: str | None
    total_tokens_used: int
    processing_time_seconds: float
```

---

## 4. Database Schema

```sql
-- ============================================
-- USERS
-- ============================================
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    name            VARCHAR(255),
    avatar_url      TEXT,
    plan            VARCHAR(20) DEFAULT 'free',        -- 'free' | 'starter' | 'pro' | 'agency'
    stripe_customer_id VARCHAR(255),
    videos_used_this_month INTEGER DEFAULT 0,
    billing_cycle_start TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- VOICE PROFILES
-- ============================================
CREATE TABLE voice_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(100) DEFAULT 'Default',    -- "My Twitter voice", "Professional", etc.
    sample_content  TEXT[] NOT NULL,                    -- Array of 3-10 past posts/content samples
    extracted_style JSONB,                             -- AI-extracted style attributes
    -- {
    --   "tone": "casual-authoritative",
    --   "sentence_length": "short-medium",
    --   "uses_emojis": false,
    --   "vocabulary_level": "accessible-expert",
    --   "signature_phrases": ["here's the thing", "let me break this down"],
    --   "formatting_style": "line-breaks-heavy"
    -- }
    is_default      BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- VIDEOS (Processing Jobs)
-- ============================================
CREATE TABLE videos (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    youtube_url     VARCHAR(500) NOT NULL,
    youtube_id      VARCHAR(20) NOT NULL,               -- Extracted video ID
    video_title     VARCHAR(500),
    channel_name    VARCHAR(255),
    duration_seconds INTEGER,
    thumbnail_url   TEXT,

    -- Processing
    status          VARCHAR(20) DEFAULT 'queued',       -- 'queued' | 'processing' | 'completed' | 'failed'
    status_detail   VARCHAR(50),                        -- 'extracting_transcript' | 'analyzing' | 'generating' | 'qa_check'
    error_message   TEXT,

    -- Raw data
    transcript      TEXT,
    analysis        JSONB,                              -- ContentAnalysis as JSON

    -- Metadata
    voice_profile_id UUID REFERENCES voice_profiles(id),
    target_platforms TEXT[] DEFAULT '{}',
    tokens_used     INTEGER DEFAULT 0,
    processing_time_ms INTEGER,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

-- ============================================
-- GENERATED CONTENT
-- ============================================
CREATE TABLE content_pieces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id        UUID REFERENCES videos(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,

    platform        VARCHAR(20) NOT NULL,               -- 'twitter' | 'linkedin' | 'newsletter' | 'blog' | 'shorts' | 'carousel'
    content_type    VARCHAR(30) NOT NULL,               -- 'standalone_tweet' | 'thread' | 'post' | 'draft' | 'script' | etc.
    content         TEXT NOT NULL,                       -- The actual generated content
    metadata        JSONB,                              -- Platform-specific metadata
    -- Twitter: { character_count, has_hook, is_thread_part, thread_position }
    -- Shorts: { timestamp_start, timestamp_end, duration }
    -- Blog: { title, meta_description, word_count, seo_keywords }

    -- User interaction
    is_favorited    BOOLEAN DEFAULT false,
    is_edited       BOOLEAN DEFAULT false,
    edited_content  TEXT,                                -- User's edited version
    is_exported     BOOLEAN DEFAULT false,
    exported_at     TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- USAGE TRACKING
-- ============================================
CREATE TABLE usage_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    video_id        UUID REFERENCES videos(id),
    action          VARCHAR(30) NOT NULL,               -- 'video_processed' | 'content_exported' | 'voice_created'
    tokens_used     INTEGER,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX idx_videos_user_id ON videos(user_id);
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_created ON videos(created_at DESC);
CREATE INDEX idx_content_video_id ON content_pieces(video_id);
CREATE INDEX idx_content_platform ON content_pieces(platform);
CREATE INDEX idx_content_user_id ON content_pieces(user_id);
CREATE INDEX idx_usage_user_month ON usage_logs(user_id, created_at);
```

---

## 5. API Contract

### 5.1 Video Processing

```
POST /api/videos/process
Authorization: Bearer <jwt>

Request:
{
    "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "platforms": ["twitter", "linkedin", "newsletter"],
    "voice_profile_id": "uuid-or-null"
}

Response (202 Accepted):
{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "queued",
    "estimated_time_seconds": 60,
    "poll_url": "/api/videos/550e8400-e29b-41d4-a716-446655440000"
}
```

```
GET /api/videos/{job_id}
Authorization: Bearer <jwt>

Response (200 — while processing):
{
    "job_id": "550e8400-...",
    "status": "processing",
    "status_detail": "generating",
    "progress": 65,
    "video_title": "Why Most Startups Fail",
    "started_at": "2026-05-23T10:30:00Z"
}

Response (200 — when complete):
{
    "job_id": "550e8400-...",
    "status": "completed",
    "video_title": "Why Most Startups Fail",
    "channel_name": "TechFounder",
    "duration_seconds": 842,
    "content_kit": {
        "twitter": {
            "standalone_tweets": [...],
            "thread": [...],
            "engagement_hooks": [...]
        },
        "linkedin": {
            "posts": [...]
        },
        "newsletter": {
            "subject_lines": [...],
            "body": "..."
        }
    },
    "analysis_summary": {
        "core_thesis": "...",
        "key_ideas_count": 5,
        "narrative_arc": "problem-solution"
    },
    "tokens_used": 12450,
    "processing_time_seconds": 47
}
```

### 5.2 Voice Profile

```
POST /api/voice-profile
Authorization: Bearer <jwt>

Request:
{
    "name": "My Twitter Voice",
    "samples": [
        "Here's what nobody tells you about fundraising...",
        "I spent 3 years building the wrong product. Thread 🧵",
        "Unpopular opinion: most startup advice is survivorship bias."
    ]
}

Response (201):
{
    "id": "...",
    "name": "My Twitter Voice",
    "extracted_style": {
        "tone": "casual-authoritative",
        "sentence_length": "short",
        "uses_emojis": true,
        "vocabulary_level": "accessible",
        "signature_phrases": ["here's what nobody tells you", "unpopular opinion"],
        "formatting_style": "hook-first-thread-style"
    }
}
```

### 5.3 History & Content

```
GET /api/history?page=1&per_page=20
Authorization: Bearer <jwt>

Response:
{
    "videos": [
        {
            "id": "...",
            "video_title": "Why Most Startups Fail",
            "youtube_url": "...",
            "thumbnail_url": "...",
            "platforms_generated": ["twitter", "linkedin"],
            "content_count": 12,
            "created_at": "2026-05-23T10:30:00Z"
        }
    ],
    "total": 45,
    "page": 1,
    "per_page": 20
}
```

```
GET /api/content/{content_id}
PUT /api/content/{content_id}          # Edit content
POST /api/content/{content_id}/export  # Export to clipboard/markdown/buffer
DELETE /api/content/{content_id}
```

---

## 6. Agent Pipeline — Deep Dive

### 6.1 Transcript Extraction Node

```
Strategy (with fallbacks):
1. youtube-transcript-api (free, fast, no API key)
   → Works for 90%+ of videos that have auto-captions
2. yt-dlp audio download + OpenAI Whisper API
   → Fallback for videos without captions
   → Adds ~$0.006/min cost
3. Manual paste
   → User can paste transcript directly if both fail
```

### 6.2 Content Analyzer — The Most Important Node

This is where the storytelling intelligence lives. The analyzer doesn't just summarize — it *deconstructs the narrative*.

```
Input: Raw transcript + video metadata

Prompt structure:
- System: "You are a content strategist who has studied viral content
  across every platform. You think in terms of narrative structure,
  emotional hooks, and platform-native formats."

- Task: Analyze this transcript and extract:
  1. CORE THESIS — One sentence: what is this video really about?
  2. KEY IDEAS — 3-8 distinct ideas, each with:
     - The idea itself
     - A supporting quote from the transcript
     - Approximate timestamp
     - Emotional weight (surprising/controversial/inspiring/practical)
  3. HOOKS — Lines that would stop someone scrolling
  4. QUOTABLE LINES — Standalone powerful statements
  5. DATA POINTS — Any numbers, stats, research referenced
  6. NARRATIVE ARC — Is this problem→solution? A story? A list? A debate?
  7. TARGET AUDIENCE — Who is the creator speaking to?
  8. EMOTIONAL JOURNEY — Map the emotional beats across the video
  9. CONTROVERSY LEVEL — How spicy is this content?

Output: Structured JSON (ContentAnalysis)
```

### 6.3 Platform Generators — Key Design Decisions

Each generator gets the same ContentAnalysis but produces radically different output.

**Twitter Generator Design:**
```
Rules baked into the prompt:
- Standalone tweets: 1 key idea = 1 tweet. Under 280 chars. Hook-first.
- Thread: Follow the "1-3-1" format (1 hook tweet, 3-5 value tweets, 1 CTA)
- No "🧵 Thread:" — that's 2023 style. Modern threads hook without announcing.
- Engagement hooks: Questions, hot takes, contrarian angles from the content
- If voice_profile provided: match the creator's sentence patterns and vocabulary
```

**LinkedIn Generator Design:**
```
Rules:
- Hook line → line break → story/insight → takeaway → soft CTA
- 150-300 words (LinkedIn sweet spot)
- Professional but not corporate
- First line is EVERYTHING — must create curiosity gap
- Use the video's data points prominently (LinkedIn loves stats)
- End with a question to drive comments
```

**Newsletter Generator Design:**
```
Rules:
- Subject line: curiosity gap or specific benefit, under 50 chars
- Opening: personal hook — not "In this video I..."
- Body: 3-4 key insights with the creator's commentary/perspective
- Each insight: one paragraph, not a bullet list
- CTA: link back to the full video
- Total: 400-600 words
```

### 6.4 Quality Assurance Node

```
The QA agent checks EVERY generated piece against these criteria:

GENERIC LANGUAGE CHECK:
  - Contains "In today's fast-paced world" → FAIL
  - Contains "Let's dive in" → FAIL
  - Contains "game-changer" → FAIL
  - More than 30% of sentences could apply to ANY video → FAIL
  → Action: send back to generator with "be more specific" instruction

VOICE CONSISTENCY CHECK (if voice profile exists):
  - Compare sentence length distribution
  - Check for signature phrases
  - Verify emoji usage matches profile
  → Action: rewrite with voice correction prompt

PLATFORM FORMAT CHECK:
  - Twitter: all tweets under 280 chars?
  - LinkedIn: has hook line + line break structure?
  - Newsletter: has subject line + proper sections?
  → Action: reformat

FACTUAL CONSISTENCY CHECK:
  - Any claims in generated content that aren't in the transcript?
  - Any stats that were altered or rounded incorrectly?
  → Action: correct or remove

Max 2 retry cycles, then pass with warnings.
```

---

## 7. Phased Roadmap

### PHASE 0 — Foundation Setup
**Duration:** Days 1-2
**Goal:** Dev environment ready, repo structured, dependencies installed

| Step | Task | Verifiable Output |
|------|------|-------------------|
| 0.1 | Create GitHub repo with the project structure above | `git clone` works, folder structure matches spec |
| 0.2 | Set up Python backend: pyproject.toml, FastAPI skeleton, uvicorn running | `curl localhost:8000/health` returns `{"status": "ok"}` |
| 0.3 | Set up Next.js frontend with Tailwind | `localhost:3000` shows a placeholder page |
| 0.4 | Set up Supabase project (DB + Auth) | Can connect to Postgres, run a test query |
| 0.5 | Create `.env.example` with all required keys | Anthropic API key, Supabase URL, etc. documented |
| 0.6 | Docker Compose for local dev (API + Redis + Postgres) | `docker-compose up` starts everything |

**Phase 0 Deliverable:** Running dev environment with empty but connected frontend + backend

---

### PHASE 1 — Core Pipeline (CLI)
**Duration:** Days 3-8
**Goal:** Working LangGraph pipeline that takes a YouTube URL and outputs Twitter + LinkedIn content — tested via CLI, no web UI yet

| Step | Task | Verifiable Output |
|------|------|-------------------|
| 1.1 | Build transcript extraction service | `python -m agents.nodes.transcript "youtube_url"` prints transcript |
| 1.2 | Design and test analyzer prompt | Feed 3 different video transcripts, verify ContentAnalysis JSON is accurate and detailed |
| 1.3 | Build analyzer node | `analyze_content(transcript)` returns valid ContentAnalysis |
| 1.4 | Design Twitter generator prompts | Test with 3 analyses, manually review output quality |
| 1.5 | Build Twitter generator node | `generate_twitter(analysis)` returns TwitterContent with 5+ tweets and a thread |
| 1.6 | Design LinkedIn generator prompts | Test with 3 analyses, manually review |
| 1.7 | Build LinkedIn generator node | `generate_linkedin(analysis)` returns LinkedInContent with 2-3 posts |
| 1.8 | Wire everything into LangGraph | `python -m agents.graph "youtube_url"` runs full pipeline end-to-end |
| 1.9 | Build QA node (basic version) | QA catches at least 1 generic phrase in test output and requests rewrite |
| 1.10 | Test with 10 real YouTube videos | All 10 produce usable output. Document quality scores (1-10) for each. |

**Phase 1 Deliverable:** `python run_pipeline.py "https://youtube.com/watch?v=xyz"` → prints formatted Twitter + LinkedIn content to terminal. Average quality score ≥ 7/10.

---

### PHASE 2 — API + Basic Frontend
**Duration:** Days 9-16
**Goal:** Web app where a user pastes a URL, waits, and sees generated content

| Step | Task | Verifiable Output |
|------|------|-------------------|
| 2.1 | Build `POST /api/videos/process` endpoint | cURL request returns job_id with 202 status |
| 2.2 | Set up Redis + async task queue (ARQ or Celery) | Job gets picked up by worker within 5 seconds |
| 2.3 | Build `GET /api/videos/{id}` with status polling | Returns status progression: queued → processing → completed |
| 2.4 | Connect LangGraph pipeline to worker | Worker runs full pipeline, saves results to Postgres |
| 2.5 | Build database models + migrations | Alembic migration runs, tables created in Supabase |
| 2.6 | Build frontend: URL input component | Paste URL → hit submit → see loading state |
| 2.7 | Build frontend: polling + progress display | Shows "Extracting transcript..." → "Analyzing..." → "Generating..." |
| 2.8 | Build frontend: content kit display | Tabbed view: Twitter | LinkedIn. Each piece in a card with copy button |
| 2.9 | Add copy-to-clipboard for each content piece | Click "Copy" → clipboard contains the content → toast confirmation |
| 2.10 | End-to-end test: paste URL in browser → get content | Full flow works in under 90 seconds for a 10-min video |

**Phase 2 Deliverable:** Working web app (no auth) — paste YouTube URL → see Twitter + LinkedIn content with copy buttons. Demo-able to potential users.

---

### PHASE 3 — All Platforms + Voice Matching
**Duration:** Days 17-24
**Goal:** Full content kit (all 6 platforms) + voice profile system

| Step | Task | Verifiable Output |
|------|------|-------------------|
| 3.1 | Build newsletter generator node + prompts | Generates newsletter with 3 subject lines + body |
| 3.2 | Build blog generator node + prompts | Generates SEO-structured blog post (800-1500 words) |
| 3.3 | Build Shorts script generator node | Generates 3-5 clip suggestions with timestamps |
| 3.4 | Build carousel generator node | Generates 6-10 slide outlines with captions |
| 3.5 | Add all generators to LangGraph (parallel execution) | Full pipeline generates all 6 platform outputs |
| 3.6 | Build voice profile API endpoint | POST samples → get back extracted style attributes |
| 3.7 | Build voice profile extraction logic | AI analyzes 3-10 content samples → extracts tone, patterns, vocabulary |
| 3.8 | Inject voice profile into generator prompts | With voice profile: output noticeably matches creator's style |
| 3.9 | Build voice profile UI (settings page) | User can paste sample content, see extracted style, save profile |
| 3.10 | Update content kit UI for all platforms | 6 tabs, each showing platform-specific content with proper formatting |
| 3.11 | Test with 5 creators' real content + voice profiles | Blind test: can someone tell the voice-matched output from the creator's real posts? |

**Phase 3 Deliverable:** Full content kit with all 6 platforms. Voice profile system working. Quality is demonstrably better than generic AI output.

---

### PHASE 4 — Auth, Payments, and Quotas
**Duration:** Days 25-32
**Goal:** Users can sign up, subscribe, and are gated by their plan limits

| Step | Task | Verifiable Output |
|------|------|-------------------|
| 4.1 | Integrate Supabase Auth (email + Google OAuth) | User can sign up and log in |
| 4.2 | Add auth middleware to all API routes | Unauthenticated requests get 401 |
| 4.3 | Build protected dashboard layout | Logged-in users see dashboard; others see landing page |
| 4.4 | Set up Lemon Squeezy (or Stripe) products | 3 plans created: Starter ($19), Pro ($29), Agency ($49) |
| 4.5 | Build checkout flow | User clicks "Upgrade" → Lemon Squeezy checkout → redirected back |
| 4.6 | Build webhook handler for payment events | subscription_created → user.plan updated in DB |
| 4.7 | Build quota enforcement | Free: 2 videos/month. Starter: 10. Pro: 30. Over quota → upgrade prompt |
| 4.8 | Build usage tracking | Dashboard shows "7/10 videos used this month" |
| 4.9 | Build billing management page | User can see plan, usage, upgrade/downgrade, cancel |
| 4.10 | Test full payment flow | Sign up → process free video → hit limit → upgrade → process more |

**Phase 4 Deliverable:** Fully gated product. Sign up → free tier (2 videos) → upgrade to paid → process videos within plan limits.

---

### PHASE 5 — Polish, Landing Page, and Launch Prep
**Duration:** Days 33-40
**Goal:** Product looks professional, landing page converts, ready for real users

| Step | Task | Verifiable Output |
|------|------|-------------------|
| 5.1 | Design and build landing page | Hero, demo video/GIF, features, pricing, social proof, CTA |
| 5.2 | Polish dashboard UI/UX | Consistent design system, loading states, empty states, error states |
| 5.3 | Build onboarding flow | New user: welcome → paste first URL → see magic → prompt to set up voice |
| 5.4 | Add video history page | User can see all past videos + regenerate content |
| 5.5 | Add export options | Download as Markdown, copy all, export to Notion (stretch) |
| 5.6 | Add error handling everywhere | Bad URLs, API failures, rate limits — all show friendly messages |
| 5.7 | Set up monitoring (Sentry + basic analytics) | Errors logged, page views tracked |
| 5.8 | Set up transactional emails (Resend) | Welcome email, payment confirmation, weekly digest |
| 5.9 | Write launch copy for Reddit, Twitter, Product Hunt | 3 platform-specific launch posts drafted |
| 5.10 | Deploy to production (Vercel + Railway/Fly.io) | Live at repost-ai.com (or whatever domain) |

**Phase 5 Deliverable:** Production-deployed, polished product with landing page. Ready to accept paying users.

---

### PHASE 6 — Growth Features (Post-Launch)
**Duration:** Ongoing
**Goal:** Retention and expansion

| Step | Task | Verifiable Output |
|------|------|-------------------|
| 6.1 | Content calendar view | User sees all generated content in a weekly calendar layout |
| 6.2 | Scheduling integration (Buffer/Typefully API) | One-click "Schedule this tweet" sends to Buffer |
| 6.3 | Batch processing | Paste a YouTube channel URL → process last 10 videos |
| 6.4 | A/B headline testing | Generate 2 versions of each piece, track which gets more copies/exports |
| 6.5 | Team features (Agency plan) | Invite team members, shared voice profiles |
| 6.6 | API access (Agency plan) | REST API for power users / integrations |
| 6.7 | Analytics dashboard | Which content got exported most, platform breakdown |

---

## Cost Estimation (Per Video Processed)

| Component | Cost |
|-----------|------|
| Transcript extraction (youtube-transcript-api) | $0.00 |
| Content Analysis (Claude Sonnet, ~2K input + 1K output) | ~$0.02 |
| 6 Platform Generators (Claude Sonnet, ~2K input + 2K output each) | ~$0.12 |
| QA Check (Claude Haiku, lightweight) | ~$0.01 |
| **Total per video** | **~$0.15** |

At $19/month for 10 videos = $1.50 cost = **92% gross margin**
At $29/month for 30 videos = $4.50 cost = **84% gross margin**

---

## Key Technical Decisions & Rationale

| Decision | Choice | Why |
|----------|--------|-----|
| Agent framework | LangGraph | You're learning it; it handles parallel nodes, retries, and state natively |
| LLM | Claude Sonnet (primary) + Haiku (QA) | Best creative writing quality; Haiku is cheap for validation tasks |
| Backend | FastAPI + Python | Same language as your agent pipeline; async-native |
| Frontend | Next.js + Tailwind | Fast to build, great DX, easy Vercel deploy |
| Database | Supabase (Postgres) | Free tier is generous; built-in auth; real-time subscriptions if needed later |
| Auth | Supabase Auth | Already using Supabase; supports Google OAuth out of the box |
| Payments | Lemon Squeezy | Handles international tax (critical for you in India); Stripe alternative |
| Task Queue | ARQ (async Redis queue) | Lighter than Celery; Python-native; perfect for this scale |
| Hosting | Railway (backend) + Vercel (frontend) | Cheap, easy deploy, good free tiers |
| Monitoring | Sentry | Free tier catches errors; essential for production |

---

*This is a living document. Update it as decisions change during build.*
