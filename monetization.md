# RePost AI — Monetization Readiness Guide

> This document is a living build guide. Every section tells you what to build,
> why it matters for getting paid users, and which steps need your personal
> judgment vs. what can be code-generated.
>
> **Legend:**
> - `[YOU]` — Requires your input, taste, or judgment. Don't skip these.
> - `[CODE]` — Implementation work. Can be AI-assisted.
> - `[TEST]` — You must manually verify this. No test suite replaces it.

---

## The Honest State of the Project

The scaffold is well-built. Auth, payments, quotas, UI, API contracts, DB schema — all
largely in place. But there is one critical problem:

**Every AI generator is a deterministic stub. The core product does not work yet.**

You have a beautiful car with no engine. A user who signs up today, pastes a YouTube
URL, and hits Submit will get fake placeholder output — not real AI-generated content.
Nothing else on this list matters until the engine runs.

---

## Ordered Build Checklist

Work top to bottom. Do not skip ahead. Each block builds on the one before it.

---

### BLOCK 1 — Make the AI Pipeline Actually Work
> Everything else is irrelevant until real Claude output flows end-to-end.

- [ ] `[CODE]` Wire `ANTHROPIC_API_KEY` from `.env` into the backend config and verify it loads at startup
- [ ] `[CODE]` Replace the deterministic analyzer stub (`agents/nodes/analyzer.py`) with a real Claude API call using the analyzer prompt from `system-design.md` section 6.2
- [ ] `[YOU]` Run the analyzer against 5 real YouTube transcripts. Read the `ContentAnalysis` JSON output. Does it correctly identify the hook, core thesis, key ideas, narrative arc? If not — iterate the prompt yourself until it does. This is your product's intelligence layer. It cannot be fully delegated.
- [ ] `[CODE]` Replace the deterministic Twitter generator stub with a real Claude API call
- [ ] `[YOU]` Run the Twitter generator against 3 different video types (tutorial, opinion/hot-take, story-driven). Read every tweet. Would you RT any of these? Are they platform-native or do they sound like a press release? Iterate the prompt.
- [ ] `[CODE]` Replace the deterministic LinkedIn generator stub with a real Claude API call
- [ ] `[YOU]` Same manual review for LinkedIn output. LinkedIn has a specific rhythm — hook line, line break, insight, soft CTA. Does the output nail that? Fix the prompt if not.
- [ ] `[CODE]` Replace the deterministic newsletter, blog, Shorts, and carousel generator stubs with real Claude API calls
- [ ] `[CODE]` Build the QA node — it checks for generic phrases ("In today's fast-paced world", "Let's dive in", "game-changer"), character limits on tweets, and factual consistency against the transcript. On failure it retries the offending generator once.
- [ ] `[TEST]` Run the full pipeline end-to-end via CLI (`python run_pipeline.py <url>`) against 10 real YouTube videos across different niches: tech, finance, fitness, productivity, storytelling, opinion. Score each output 1-10 for usefulness. Target average ≥ 7. Do not move to Block 2 until you hit that bar.
- [ ] `[YOU]` Document what's failing in the 3-star outputs. Is it the analyzer not extracting good hooks? Is it the Twitter generator being too safe? Identify the weak node and fix its prompt. This is the most important work in the entire project.

---

### BLOCK 2 — Make the Infrastructure Actually Run
> The API and frontend exist but the plumbing hasn't been tested live.

- [ ] `[CODE]` Run the Phase 2 Postgres migration against local Docker Postgres (`docker compose up -d postgres redis` then run the SQL migration file)
- [ ] `[CODE]` Wire real transcript fetching (`youtube-transcript-api`) into the default pipeline flow, not just the CLI extra path
- [ ] `[CODE]` Test the ARQ worker end-to-end with Redis enabled (`USE_REDIS_QUEUE=true`) — submit a job via API, confirm the worker picks it up, runs the real pipeline, and writes results to Postgres
- [ ] `[TEST]` Full browser flow: open the frontend, paste a real YouTube URL, watch the polling states ("Extracting..." → "Analyzing..." → "Generating..."), and confirm real AI-generated content appears in the content kit tabs. This is the first time you'll see the real product.
- [ ] `[YOU]` Use it. Actually use the product for your own content or a creator you follow. Note every moment of friction, confusion, or disappointment. These are your product bugs.

---

### BLOCK 3 — Voice Profile (the Feature That Justifies the Price)
> Generic AI output is free on ChatGPT. Voice matching is what makes someone pay $25/month.

- [ ] `[CODE]` Build the frontend voice profile settings flow — a form where the user pastes 3-10 of their past posts/tweets, hits Save, and sees the extracted style attributes (tone, sentence length, signature phrases)
- [ ] `[YOU]` Test voice matching with your own writing samples or a creator you know well. Paste real past tweets/posts. Generate content from a video. Read the output side by side with their actual writing. Can you tell the AI tried to match the voice? If no — the voice injection in the generator prompts needs work. Fix it.
- [ ] `[TEST]` Blind test: give a non-technical person 5 AI-generated posts (with voice matching on) and 5 real posts from the same creator. Can they tell the difference less than 70% of the time? If yes — voice matching is working. If they can always tell — keep iterating.

---

### BLOCK 4 — Confirm Auth and Payments Work Live
> These were built but haven't been smoke-tested against real external services.

- [ ] `[TEST]` Create a real test account via the signup flow (email). Confirm the welcome experience makes sense.
- [ ] `[TEST]` Test Google OAuth login — works end-to-end?
- [ ] `[TEST]` Process 2 videos on the free tier. Hit the quota. Confirm the upgrade prompt appears and is compelling — not just a generic "You've hit your limit" wall.
- [ ] `[YOU]` Write the upgrade prompt copy yourself. This is a conversion moment. The message a user sees when they hit their quota limit is one of the highest-leverage pieces of copy in the product. It should remind them of the value they just got, not just tell them they're blocked.
- [ ] `[TEST]` Complete a real Lemon Squeezy checkout (use test mode). Confirm the webhook fires, user plan updates in DB, and quota resets to the new plan's limit.
- [ ] `[TEST]` Check the billing management page. Can you see your plan, usage, and upgrade/cancel options without confusion?

---

### BLOCK 5 — Production Deployment
> The product doesn't exist for paying users until it has a URL.

- [ ] `[CODE]` Deploy frontend to Vercel — connect repo, set environment variables, confirm build passes
- [ ] `[CODE]` Deploy backend to Railway or Fly.io — Dockerfile exists, set env vars, confirm `/health` responds on production URL
- [ ] `[CODE]` Set up production Postgres (Supabase) and run all migrations against it
- [ ] `[CODE]` Set up production Redis instance (Railway Redis or Upstash)
- [ ] `[CODE]` Connect production domain (repostai.com or similar)
- [ ] `[CODE]` Set up Sentry on both frontend and backend — you need to know when production is broken before your users do
- [ ] `[CODE]` Set up Resend transactional emails: welcome email on signup, payment confirmation on upgrade, failed payment notice
- [ ] `[YOU]` Write the welcome email yourself. The first email a paying user gets sets the tone for your entire relationship with them. It should not sound like it was written by a robot. Tell them exactly what they can do, what to try first, and how to reach you if something breaks.
- [ ] `[TEST]` Full end-to-end smoke test on production: sign up → process a video → see content → upgrade → process more videos. If this works cleanly, you have a product.

---

### BLOCK 6 — Landing Page That Converts
> The landing page is built but it's missing the one thing that makes people sign up: proof that it works.

- [ ] `[YOU]` Record a demo. It doesn't need to be polished. 60-90 seconds: paste a URL, watch it process, show the Twitter thread and LinkedIn post output. Real video, real content, real output. This is non-negotiable — without it, visitors read about a feature and leave. With it, they see the magic and sign up.
- [ ] `[CODE]` Embed the demo video/GIF prominently on the landing page hero — above the fold, before any feature list
- [ ] `[YOU]` Get 3 real people (YouTubers or content creators, even small ones) to try the product before you launch publicly. Offer them free Pro access for a month. Collect their honest reaction. If they say "wow that's actually good" — ask for a quote. If they say "meh" — you have more work to do on output quality.
- [ ] `[YOU]` Write the social proof section using their real quotes. Fake testimonials are obvious and destroy trust with the exact audience (savvy creators) you're targeting.
- [ ] `[YOU]` Read your own landing page copy from the perspective of a US YouTuber with 10K subscribers who has never heard of you. Does the hero line immediately communicate what the product does and why it's worth $19/month? If you have to think about it — rewrite it.

---

### BLOCK 7 — Launch
> Only start this block after Block 5 is fully green.

- [ ] `[YOU]` Post on relevant subreddits (r/NewTubers, r/youtubers, r/contentcreator) — the launch copy is drafted, but read it again before posting. Does it feel like a real founder sharing something useful, or does it feel like an ad? Rewrite anything that sounds like an ad.
- [ ] `[YOU]` Post on Twitter/X. Tag 3-5 mid-size creators in your niche (not megastars — people who might actually reply). Reply to their content genuinely before pitching.
- [ ] `[YOU]` Submit to Product Hunt. Choose your launch day carefully (Tuesday/Wednesday performs best). Be available all day to respond to comments.
- [ ] `[CODE]` Set up basic analytics (PostHog or Plausible) — you need to know: how many people visit, how many sign up, how many process a video, how many upgrade. Without this you're flying blind.

---

## What NOT to Build Before Launch

These are real features in the roadmap but they are post-revenue work. Building them
now is procrastination dressed as productivity:

- Buffer/Typefully scheduling integration
- Batch processing for channels
- Team invitations and shared voice profiles
- Notion export
- A/B testing infrastructure
- Agency plan team seats

Do these after your first 10 paying customers tell you what they actually want.

---

## The Quality Bar for Paying Users

A Western YouTuber will pay $20-25/month if — and only if — the output clears this bar:

1. **It doesn't sound like AI.** If someone reads the Twitter thread and thinks "ChatGPT wrote this," they won't pay. The output needs to feel crafted, specific to that video, not template-filled.

2. **It saves real time.** The alternative is 2-3 hours of writing per video. If using your tool takes 5 minutes to review and edit the output, that's a clear ROI. If it takes 45 minutes of editing because the output is mediocre, it's not worth it.

3. **Voice matching is noticeably real.** This is your moat. Generic repurposing tools exist. A tool that sounds like *them* is what justifies the subscription.

4. **It works reliably.** One broken pipeline on a launch day for a creator will earn a public complaint. Production monitoring (Sentry) and a fallback for transcript failures are not optional.

---

## Cost Reality Check (Keep This in Mind)

| Plan | Price | Videos | AI Cost | Gross Margin |
|------|-------|--------|---------|--------------|
| Starter | $19/mo | 10 | ~$1.50 | ~92% |
| Pro | $29/mo | 30 | ~$4.50 | ~84% |
| Agency | $49/mo | unlimited | ~$15 est. | ~70% |

The unit economics are excellent. The only risk is output quality — if quality is low,
no one renews month 2, regardless of how good the infrastructure is.

---

## Summary: The Real Remaining Work

| Block | Effort | Who Does It | Blocks Revenue? |
|-------|--------|-------------|----------------|
| 1 — Real AI pipeline + quality | 3-4 weeks | You + AI | YES — #1 blocker |
| 2 — Infrastructure runs live | 3-5 days | Mostly AI | YES |
| 3 — Voice profile frontend + quality | 1 week | You + AI | Soft blocker |
| 4 — Auth/payments smoke test | 2-3 days | You | YES |
| 5 — Production deployment | 3-5 days | Mostly AI | YES |
| 6 — Landing page with real demo | 3-5 days | You (demo) + AI | YES |
| 7 — Launch | Ongoing | You | — |

**Realistic timeline to first paying customer: 6-8 weeks** if Block 1 output quality
comes together in the first 2 weeks. The prompt engineering in Block 1 is the only
genuinely unpredictable variable. Everything else is predictable engineering work.
