# RePost AI - Product Launch Copy Assets

This document contains highly optimized, copy-pasteable launch assets for our public releases.

---

## 1. Product Hunt Launch Kit

### PH Listing Metadata
* **Product Name:** RePost AI
* **Tagline:** Repurpose YouTube videos into complete social campaigns in 60s 🚀
* **Primary Topic:** Artificial Intelligence, SaaS, Creators, Marketing
* **Keywords:** YouTube, Repurposing, Content Agent, Twitter, LinkedIn, Newsletter

### PH Description (Under 250 characters)
Paste a YouTube URL. Our narrative AI agent parses the emotional hook, narrative arc, and key insights to compile a premium copy campaign for Twitter, LinkedIn, Newsletters, Blogs, Shorts scripts, and Carousels. Learn your unique voice!

### Maker's Launch Comment (First Comment on PH Listing)
```text
Hey hunters! 🚀

I'm Yuvraj, the creator of RePost AI. 

As a developer and creator, I found a massive bottleneck: editing a 10-minute video takes hours, but translating that video into engaging text campaigns for Twitter, LinkedIn, newsletters, and blogs takes even longer. Hiring agencies is expensive ($1k-$3k/mo), and generic AI summaries sound incredibly robotic and corporate.

RePost AI was built to solve this. Instead of simple GPT summaries, we designed an agentic LangGraph pipeline that thinks like a master storyteller. It identifies the hook, the narrative tension, the supporting quote, and the payoff beat in your video transcript.

Key Capabilities we shipped today:
1. 🧠 Smart Narrative Analyzer: Maps the emotional beats and narrative arc of your transcript.
2. 🗣️ Voice Style Attributes: Paste 3-5 past writing samples and the agent injects your unique sentence pacing, emoticons, and vocabulary.
3. 📦 Complete Platform Expansion: Generates standalone tweets, threads, LinkedIn posts, blogs, newsletter drafts, carousel slides, and vertical Shorts timestamp scripts.
4. 💾 Local Developer Sandbox & Exporters: Instantly download formatted Markdown copy kits or copy to clipboard.

We have a 100% free plan (no credit card needed) so you can convert your first 2 videos right now.

I would love to get your feedback, answer any questions, and hear what platform integrations we should prioritize next! 

Cheers,
Yuvraj
```

---

## 2. Twitter/X Launch Thread

### Tweet 1 (The Hook)
```text
Video editing takes 5 hours.
Writing the social promotional copy takes another 3.
Hiring a content agency costs $2,000/month.

I got tired of the bottleneck, so I built an AI Agent that translates any YouTube URL into an entire, voice-matched social campaign in 60 seconds.

Introducing RePost AI 🧵👇
[Link to repost-ai]
```

### Tweet 2 (Why GPT summaries fail)
```text
Most AI summaries sound like robotic corporate brochures. They scream "AI generated".

Why? Because they don't understand *storytelling*.

RePost AI deconstructs the narrative arc (problem-solution, listicle, story) and parses the emotional beats to write native platform copy. 🧠
```

### Tweet 3 (Platform Expansion)
```text
One YouTube URL yields:
- 5 Standalone tweets + 1 Engagement Thread 🐦
- 3 LinkedIn hook-driven posts 💼
- 1 Personal newsletter draft ( intro → insights → CTA) 📧
- 1 SEO Blog post with meta descriptions 📝
- 3 Shorts clip timestamps with script drafts 🎥
- 1 Instagram carousel outline 📸
```

### Tweet 4 (Voice Profiles)
```text
Unpopular opinion: GPT-4 writes like a middle-manager.

We fixed this. With Voice Style Profiles, you paste 3-5 past writing samples. Our agent extracts your sentence structures, signature phrases, and emoticons to match your voice exactly. 🗣️
```

### Tweet 5 (Interactive Demo)
```text
Our entire pipeline runs on a self-healing local fallback database, gates monthly quotas automatically, and exports beautifully formatted Markdown campaigns with a single click.

Here is a quick look at the workspace in action:
[GIF / Screenshot of Workspace]
```

### Tweet 6 (CTA / Wrap up)
```text
Best part? It’s completely free to start. 

Convert your first 2 videos today with no credit card required:
👉 [Link to signup]

Let me know what you think in the comments!
```

---

## 3. Reddit Launch Post

### Subreddits: `r/SideProject`, `r/saas`, `r/creators`

### Title
```text
I built an AI agent that turns any YouTube URL into a complete, voice-matched social campaign in 60s (Built with Next.js, FastAPI & LangGraph)
```

### Body
```text
Hey guys,

I wanted to share a project I've been working on called RePost AI. 

As someone who publishes video content, I realized I was leaving a massive amount of reach on the table by not translating my YouTube videos into text campaigns for Twitter, LinkedIn, newsletters, and blogs. But doing it manually took hours, and hiring an agency was way too expensive.

I tried generic AI summary tools, but the output always sounded like a generic corporate PDF. They lacked hooks, had no pacing, and used generic phrases like "In today's fast-paced world."

So I built RePost AI. 

How it works technically:
- Frontend: Next.js + Tailwind CSS (v4) with interactive step-by-step onboarding walkthroughs.
- Backend: FastAPI + SQLAlchemy (Async Postgres database) + Redis / ARQ task queues.
- LLM Pipeline: Built with LangGraph. It runs transcript extraction → narrative analyzer node (extracts core thesis, support quotes, emotional beats) → parallel platform generators → QA agent loop (max 2 retries to filter out generic AI words) → PostgreSQL/SQLite store.

Resilient Local Developer Features we baked in:
- Self-Healing DB: If Postgres is not running during local testing, the backend automatically fallbacks to a local async SQLite database (`aiosqlite`) so you don't even need Docker to test.
- Voice Profile Attribute Injector: Paste past posts to extract sentence pacing and signature phrases.
- One-Click Exporters: Download the entire Campaign Kit as a beautifully formatted `.md` file.
- Payment Simulation Sandbox: Try the complete signup-to-paid quota upgrade flow in local dev with a sandbox simulator panel.

It has a free tier (2 videos/month) to convert your videos immediately.

Check it out here: [Link to repost-ai]

I'd love to hear your feedback on the UX, output quality, or any technical questions you have about the LangGraph pipeline architecture!
```
