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
- [ ] Replace deterministic analyzer with LLM-backed analyzer prompt
- [ ] Replace deterministic Twitter/X generator with LLM-backed generator prompt
- [ ] Replace deterministic LinkedIn generator with LLM-backed generator prompt
- [ ] Add basic QA node
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
- [ ] Switch default job persistence from JSON store to Postgres repository
- [ ] Run ARQ worker end-to-end with Redis enabled
- [ ] Add browser end-to-end test for paste URL to rendered content
- [ ] Wire real transcript fetching into default local flow after installing transcript extra

## Phase 3 - All Platforms + Voice Matching

- [ ] Build newsletter generator schema
- [ ] Build newsletter generator node and prompts
- [ ] Build blog generator schema
- [ ] Build blog generator node and prompts
- [ ] Build YouTube Shorts script schema
- [ ] Build Shorts generator node and timestamp contract
- [ ] Build Instagram carousel schema
- [ ] Build carousel generator node and prompts
- [ ] Add all platform generators to pipeline
- [ ] Run platform generators in parallel where practical
- [ ] Build voice profile request/response schema
- [ ] Build voice profile extraction logic
- [ ] Add voice profile persistence model
- [ ] Add voice profile API endpoint
- [ ] Inject voice profile into generator context
- [ ] Build frontend voice profile settings flow
- [ ] Expand frontend content kit tabs for all platforms
- [ ] Test output with five creator voice profiles

## Phase 4 - Auth, Payments, and Quotas

- [ ] Integrate Supabase Auth
- [ ] Add email login
- [ ] Add Google OAuth login
- [ ] Add auth middleware for protected API routes
- [ ] Add protected dashboard layout
- [ ] Add user model and profile data
- [ ] Add plan/quota model
- [ ] Add free tier quota enforcement
- [ ] Add usage tracking per user/month
- [ ] Add dashboard usage display
- [ ] Set up Lemon Squeezy or Stripe products
- [ ] Add checkout flow
- [ ] Add payment webhook handler
- [ ] Update user plan from webhook events
- [ ] Add billing management page
- [ ] Test full signup to paid upgrade flow

## Phase 5 - Polish, Landing Page, and Launch Prep

- [ ] Design and build landing page
- [ ] Add demo video or GIF section
- [ ] Add pricing section
- [ ] Add social proof/testimonial section
- [ ] Polish dashboard UI and empty states
- [ ] Polish loading and error states
- [ ] Build onboarding flow
- [ ] Build video history page
- [ ] Add regenerate content flow
- [ ] Add Markdown export
- [ ] Add copy-all export
- [ ] Add Notion export research or integration
- [ ] Add friendly handling for bad URLs
- [ ] Add friendly handling for transcript failures
- [ ] Add rate-limit error UI
- [ ] Set up Sentry
- [ ] Add basic analytics
- [ ] Set up Resend transactional emails
- [ ] Draft launch copy for Reddit
- [ ] Draft launch copy for Twitter/X
- [ ] Draft launch copy for Product Hunt
- [ ] Deploy frontend to Vercel
- [ ] Deploy backend to Railway/Fly.io
- [ ] Connect production domain

## Phase 6 - Growth Features

- [ ] Build content calendar view
- [ ] Add Buffer scheduling integration
- [ ] Add Typefully scheduling integration
- [ ] Add batch processing for channel URLs
- [ ] Add A/B headline generation
- [ ] Track copy/export analytics
- [ ] Add team invitations
- [ ] Add shared voice profiles
- [ ] Add Agency plan API access
- [ ] Build analytics dashboard

