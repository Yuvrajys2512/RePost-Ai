CREATE TABLE IF NOT EXISTS video_jobs (
    id UUID PRIMARY KEY,
    youtube_url TEXT NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'queued',
    status_detail TEXT NOT NULL,
    progress INTEGER NOT NULL DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    transcript_text TEXT,
    error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS generated_content (
    id UUID PRIMARY KEY,
    video_job_id UUID NOT NULL REFERENCES video_jobs(id) ON DELETE CASCADE,
    platform VARCHAR(32) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_video_jobs_status ON video_jobs(status);
CREATE INDEX IF NOT EXISTS idx_video_jobs_created_at ON video_jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_generated_content_video_job_id ON generated_content(video_job_id);

