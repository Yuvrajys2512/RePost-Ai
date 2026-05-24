# RePost AI Progress

## Phase 0 - Foundation Setup

- [x] Create repo structure for backend, frontend, infrastructure, and docs
- [x] Set up FastAPI backend skeleton
- [x] Add `/health` endpoint
- [x] Set up Next.js frontend scaffold
- [x] Add Tailwind/global styling foundation
- [x] Add Docker Compose for Postgres and Redis
- [x] Add `.env.example` with backend, frontend, database, Redis, AI provider, auth, billing, and monitoring variables
- [x] Add basic backend health test
- [ ] Confirm Supabase project connection against a live Postgres instance

## Phase 1 - Core Pipeline CLI

- [x] Add transcript schemas
- [x] Add transcript extraction service contract
- [x] Add YouTube URL video-id parsing
- [x] Add optional `youtube-transcript-api` integration path
- [x] Add local transcript text override for deterministic testing
- [x] Add analyzer schema
- [x] Add deterministic analyzer node before real LLM calls
- [x] Add Twitter/X generator schema
- [x] Add deterministic Twitter/X generator node
- [x] Add LinkedIn generator schema
- [x] Add deterministic LinkedIn generator node
- [x] Add generated content kit schema
- [x] Add pipeline runner contract
- [x] Add CLI transcript command
- [x] Add CLI pipeline command
- [x] Add tests for transcript parsing, analyzer output, generator output, and end-to-end CLI pipeline contracts
- [x] Replace deterministic analyzer with LLM-backed analyzer prompt
- [x] Replace deterministic Twitter/X generator with LLM-backed generator prompt
- [x] Replace deterministic LinkedIn generator with LLM-backed generator prompt
- [x] Replace deterministic newsletter, blog, Shorts, and carousel generators with LLM-backed prompts
- [x] Add basic QA node
- [ ] Test pipeline against 10 real YouTube videos
- [ ] Document quality scores for test videos

## Phase 2 - API + Basic Frontend

- [x] Build `POST /api/videos/process`
- [x] Build `GET /api/videos/{id}`
- [x] Add job status/progress response contract
- [x] Add generated content response contract
- [x] Add background pipeline dispatch path
- [x] Add local durable JSON job store for development
- [x] Add optional ARQ/Redis queue dispatch wiring
- [x] Add ARQ worker entrypoint
- [x] Add SQLAlchemy base model setup
- [x] Add `video_jobs` model
- [x] Add `generated_content` model
- [x] Add first SQL migration for Phase 2 tables
- [x] Add API tests for process and poll flow
- [x] Add infrastructure tests for local job persistence and model registration
- [x] Build frontend URL input flow
- [x] Add frontend polling
- [x] Add progress display
- [x] Add Twitter/X content tab
- [x] Add LinkedIn content tab
- [x] Add copy buttons
- [x] Verify backend lint
- [x] Verify backend tests
- [x] Verify frontend production build
- [x] Live smoke test API process/poll completion
- [ ] Run Postgres migration against local Docker Postgres
- [x] Switch default job persistence from JSON store to Postgres repository
- [ ] Run ARQ worker end-to-end with Redis enabled
- [ ] Add browser end-to-end test for paste URL to rendered content
- [x] Wire real transcript fetching into default local flow after installing transcript extra

## Phase 3 - All Platforms + Voice Matching

- [x] Build newsletter generator schema
- [x] Build newsletter generator node and deterministic prompt contract
- [x] Build blog generator schema
- [x] Build blog generator node and deterministic prompt contract
- [x] Build YouTube Shorts script schema
- [x] Build Shorts generator node and timestamp contract
- [x] Build Instagram carousel schema
- [x] Build carousel generator node and deterministic prompt contract
- [x] Add all platform generators to pipeline
- [x] Run platform generators in parallel where practical
- [x] Build voice profile request/response schema
- [x] Build voice profile extraction logic
- [x] Add voice profile persistence model
- [x] Add voice profile API endpoint
- [x] Inject voice profile into generator context
- [x] Build frontend voice profile settings flow
- [x] Expand frontend content kit tabs for all platforms
- [ ] Test output with five creator voice profiles

## Phase 4 - Auth, Payments, and Quotas

- [x] Integrate Supabase Auth
- [x] Add email login
- [x] Add Google OAuth login
- [x] Add auth middleware for protected API routes
- [x] Add protected dashboard layout
- [x] Add user model and profile data
- [x] Add plan/quota model
- [x] Add free tier quota enforcement
- [x] Add usage tracking per user/month
- [x] Add dashboard usage display
- [x] Set up Lemon Squeezy or Stripe products
- [x] Add checkout flow
- [x] Add payment webhook handler
- [x] Update user plan from webhook events
- [x] Add billing management page
- [x] Test full signup to paid upgrade flow

## Phase 5 - Polish, Landing Page, and Launch Prep

- [x] Design and build landing page
- [ ] Add demo video or GIF section
- [x] Add pricing section
- [x] Add social proof/testimonial section
- [x] Polish dashboard UI and empty states
- [x] Polish loading and error states
- [x] Build onboarding flow
- [x] Build video history page
- [x] Add regenerate content flow
- [x] Add Markdown export
- [x] Add copy-all export
- [ ] Add Notion export research or integration
- [x] Add friendly handling for bad URLs
- [x] Add friendly handling for transcript failures
- [x] Add rate-limit error UI
- [x] Set up Sentry
- [x] Add basic analytics
- [x] Set up Resend transactional emails
- [x] Draft launch copy for Reddit
- [x] Draft launch copy for Twitter/X
- [x] Draft launch copy for Product Hunt
- [ ] Deploy frontend to Vercel  [YOU — needs Vercel login + env vars set]
- [ ] Deploy backend to Railway/Fly.io  [YOU — needs Railway login + env vars set]
- [ ] Connect production domain  [YOU]

## Phase 6 - Growth Features

- [x] Build content calendar view
- [ ] Add Buffer scheduling integration
- [ ] Add Typefully scheduling integration
- [ ] Add batch processing for channel URLs
- [x] Add A/B headline generation
- [x] Track copy/export analytics
- [ ] Add team invitations
- [ ] Add shared voice profiles
- [x] Add Agency plan API access
- [x] Build analytics dashboard

