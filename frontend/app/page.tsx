"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

type JobStatus = "queued" | "processing" | "completed" | "failed";

type Tweet = {
  text: string;
};

type LinkedInPost = {
  hook: string;
  body: string;
  cta: string;
};

type NewsletterContent = {
  subject_lines: string[];
  preview_text: string;
  body: string;
  cta: string;
};

type BlogContent = {
  title: string;
  meta_description: string;
  introduction: string;
  sections: {
    heading: string;
    body: string;
  }[];
  conclusion: string;
};

type ShortsContent = {
  clips: {
    title: string;
    start_seconds: number;
    end_seconds: number;
    hook: string;
    script: string;
  }[];
};

type CarouselContent = {
  title: string;
  slides: {
    slide_number: number;
    headline: string;
    body: string;
  }[];
  caption: string;
};

type ContentKit = {
  twitter: {
    standalone_tweets: Tweet[];
    thread: Tweet[];
  };
  linkedin: {
    posts: LinkedInPost[];
  };
  newsletter: NewsletterContent;
  blog: BlogContent;
  shorts: ShortsContent;
  carousel: CarouselContent;
};

type ProcessResponse = {
  job_id: string;
  status: JobStatus;
  poll_url: string;
};

type JobResponse = {
  job_id: string;
  status: JobStatus;
  status_detail: string;
  progress: number;
  youtube_url: string;
  content: ContentKit | null;
  error: string | null;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
type ContentView = "twitter" | "linkedin" | "newsletter" | "blog" | "shorts" | "carousel";
const contentViews: { key: ContentView; label: string }[] = [
  { key: "twitter", label: "Twitter/X" },
  { key: "linkedin", label: "LinkedIn" },
  { key: "newsletter", label: "Newsletter" },
  { key: "blog", label: "Blog" },
  { key: "shorts", label: "Shorts" },
  { key: "carousel", label: "Carousel" },
];

export default function Home() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [transcriptText, setTranscriptText] = useState("");
  const [job, setJob] = useState<JobResponse | null>(null);
  const [pollUrl, setPollUrl] = useState<string | null>(null);
  const [selectedView, setSelectedView] = useState<ContentView>("twitter");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  useEffect(() => {
    if (!pollUrl || job?.status === "completed" || job?.status === "failed") {
      return;
    }

    let cancelled = false;
    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}${pollUrl}`);
        if (!response.ok) {
          throw new Error("Could not load job status");
        }
        const nextJob = (await response.json()) as JobResponse;
        if (!cancelled) {
          setJob(nextJob);
          setError(nextJob.error);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load job status");
        }
      }
    };

    poll();
    const timer = window.setInterval(poll, 1500);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [job?.status, pollUrl]);

  const canSubmit = useMemo(() => youtubeUrl.trim().length > 0 && !isSubmitting, [
    isSubmitting,
    youtubeUrl,
  ]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit) {
      return;
    }

    setIsSubmitting(true);
    setError(null);
    setCopiedKey(null);
    setJob(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/videos/process`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          youtube_url: youtubeUrl,
          platforms: ["twitter", "linkedin", "newsletter", "blog", "shorts", "carousel"],
          transcript_text: transcriptText.trim() || undefined,
        }),
      });

      if (!response.ok) {
        throw new Error("Could not start video processing");
      }

      const data = (await response.json()) as ProcessResponse;
      setPollUrl(data.poll_url);
      setJob({
        job_id: data.job_id,
        status: data.status,
        status_detail: "Queued for transcript extraction",
        progress: 0,
        youtube_url: youtubeUrl,
        content: null,
        error: null,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start video processing");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function copyText(key: string, text: string) {
    await navigator.clipboard.writeText(text);
    setCopiedKey(key);
    window.setTimeout(() => setCopiedKey(null), 1400);
  }

  return (
    <main className="min-h-screen bg-[var(--background)] px-4 py-6 text-[var(--foreground)] sm:px-6">
      <section className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-4 border-b border-[var(--border)] pb-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase text-[var(--accent)]">RePost AI</p>
            <h1 className="mt-2 text-3xl font-semibold">Content repurposing workspace</h1>
          </div>
          <span className="w-fit border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm text-[var(--muted)]">
            Phase 2
          </span>
        </header>

        <section className="grid gap-5 lg:grid-cols-[0.95fr_1.35fr]">
          <form
            className="border border-[var(--border)] bg-[var(--panel)] p-5"
            onSubmit={handleSubmit}
          >
            <label className="text-sm font-medium" htmlFor="youtube-url">
              YouTube URL
            </label>
            <input
              id="youtube-url"
              className="mt-3 min-h-11 w-full border border-[var(--border)] bg-white px-3 outline-none focus:border-[var(--accent)]"
              onChange={(event) => setYoutubeUrl(event.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              type="url"
              value={youtubeUrl}
            />

            <label className="mt-5 block text-sm font-medium" htmlFor="transcript-text">
              Transcript override
            </label>
            <textarea
              id="transcript-text"
              className="mt-3 min-h-36 w-full resize-y border border-[var(--border)] bg-white px-3 py-2 outline-none focus:border-[var(--accent)]"
              onChange={(event) => setTranscriptText(event.target.value)}
              placeholder="Optional local transcript text for deterministic testing."
              value={transcriptText}
            />

            <button
              className="mt-5 min-h-11 w-full bg-[var(--accent)] px-5 font-medium text-white hover:bg-[var(--accent-strong)] disabled:cursor-not-allowed disabled:bg-[var(--disabled)]"
              disabled={!canSubmit}
              type="submit"
            >
              {isSubmitting ? "Starting..." : "Generate content kit"}
            </button>

            {error ? (
              <p className="mt-4 border border-[var(--danger)] bg-[var(--danger-soft)] px-3 py-2 text-sm text-[var(--danger)]">
                {error}
              </p>
            ) : null}
          </form>

          <section className="border border-[var(--border)] bg-[var(--panel)] p-5">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-lg font-semibold">Pipeline status</h2>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  {job?.status_detail ?? "Waiting for a video URL"}
                </p>
              </div>
              <span className="w-fit border border-[var(--border)] px-3 py-1 text-sm capitalize text-[var(--muted)]">
                {job?.status ?? "idle"}
              </span>
            </div>

            <div className="mt-5 h-2 w-full bg-[var(--track)]">
              <div
                className="h-2 bg-[var(--accent)] transition-[width]"
                style={{ width: `${job?.progress ?? 0}%` }}
              />
            </div>

            {job?.content ? (
              <ContentResults
                content={job.content}
                copiedKey={copiedKey}
                onCopy={copyText}
                selectedView={selectedView}
                setSelectedView={setSelectedView}
              />
            ) : (
              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                {["Extracting", "Analyzing", "Generating"].map((step) => (
                  <div className="border border-[var(--border)] px-3 py-4" key={step}>
                    <p className="text-sm font-medium">{step}</p>
                    <p className="mt-2 text-sm text-[var(--muted)]">Pending</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        </section>
      </section>
    </main>
  );
}

function ContentResults({
  content,
  copiedKey,
  onCopy,
  selectedView,
  setSelectedView,
}: {
  content: ContentKit;
  copiedKey: string | null;
  onCopy: (key: string, text: string) => Promise<void>;
  selectedView: ContentView;
  setSelectedView: (view: ContentView) => void;
}) {
  return (
    <div className="mt-6">
      <div className="grid grid-cols-2 border border-[var(--border)] md:grid-cols-3 xl:grid-cols-6">
        {contentViews.map((view) => (
          <button
            className={tabClass(selectedView === view.key)}
            key={view.key}
            onClick={() => setSelectedView(view.key)}
            type="button"
          >
            {view.label}
          </button>
        ))}
      </div>

      {selectedView === "twitter" && (
        <TwitterResults content={content} copiedKey={copiedKey} onCopy={onCopy} />
      )}
      {selectedView === "linkedin" && (
        <LinkedInResults content={content} copiedKey={copiedKey} onCopy={onCopy} />
      )}
      {selectedView === "newsletter" && (
        <NewsletterResults content={content.newsletter} copiedKey={copiedKey} onCopy={onCopy} />
      )}
      {selectedView === "blog" && (
        <BlogResults content={content.blog} copiedKey={copiedKey} onCopy={onCopy} />
      )}
      {selectedView === "shorts" && (
        <ShortsResults content={content.shorts} copiedKey={copiedKey} onCopy={onCopy} />
      )}
      {selectedView === "carousel" && (
        <CarouselResults content={content.carousel} copiedKey={copiedKey} onCopy={onCopy} />
      )}
    </div>
  );
}

function TwitterResults({
  content,
  copiedKey,
  onCopy,
}: {
  content: ContentKit;
  copiedKey: string | null;
  onCopy: (key: string, text: string) => Promise<void>;
}) {
  const threadText = content.twitter.thread.map((tweet) => tweet.text).join("\n\n");

  return (
    <div className="mt-5 grid gap-5 xl:grid-cols-2">
      <section>
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-semibold">Standalone tweets</h3>
        </div>
        <div className="mt-3 grid gap-3">
          {content.twitter.standalone_tweets.map((tweet, index) => (
            <article className="border border-[var(--border)] p-3" key={`${tweet.text}-${index}`}>
              <p className="text-sm leading-6">{tweet.text}</p>
              <button
                className="mt-3 border border-[var(--border)] px-3 py-1 text-sm hover:border-[var(--accent)]"
                onClick={() => onCopy(`tweet-${index}`, tweet.text)}
                type="button"
              >
                {copiedKey === `tweet-${index}` ? "Copied" : "Copy"}
              </button>
            </article>
          ))}
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-semibold">Thread</h3>
          <button
            className="border border-[var(--border)] px-3 py-1 text-sm hover:border-[var(--accent)]"
            onClick={() => onCopy("thread", threadText)}
            type="button"
          >
            {copiedKey === "thread" ? "Copied" : "Copy all"}
          </button>
        </div>
        <ol className="mt-3 grid gap-3">
          {content.twitter.thread.map((tweet, index) => (
            <li className="border border-[var(--border)] p-3 text-sm leading-6" key={index}>
              <span className="mr-2 text-[var(--muted)]">{index + 1}.</span>
              {tweet.text}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function LinkedInResults({
  content,
  copiedKey,
  onCopy,
}: {
  content: ContentKit;
  copiedKey: string | null;
  onCopy: (key: string, text: string) => Promise<void>;
}) {
  return (
    <div className="mt-5 grid gap-4">
      {content.linkedin.posts.map((post, index) => {
        const text = `${post.hook}\n\n${post.body}\n\n${post.cta}`;
        return (
          <article className="border border-[var(--border)] p-4" key={`${post.hook}-${index}`}>
            <p className="font-semibold">{post.hook}</p>
            <p className="mt-3 whitespace-pre-wrap text-sm leading-6">{post.body}</p>
            <p className="mt-3 text-sm font-medium">{post.cta}</p>
            <button
              className="mt-4 border border-[var(--border)] px-3 py-1 text-sm hover:border-[var(--accent)]"
              onClick={() => onCopy(`linkedin-${index}`, text)}
              type="button"
            >
              {copiedKey === `linkedin-${index}` ? "Copied" : "Copy"}
            </button>
          </article>
        );
      })}
    </div>
  );
}

function NewsletterResults({
  content,
  copiedKey,
  onCopy,
}: {
  content: NewsletterContent;
  copiedKey: string | null;
  onCopy: (key: string, text: string) => Promise<void>;
}) {
  const text = `Subject options:\n${content.subject_lines.join("\n")}\n\n${content.preview_text}\n\n${content.body}\n\n${content.cta}`;
  return (
    <section className="mt-5 border border-[var(--border)] p-4">
      <h3 className="font-semibold">Newsletter draft</h3>
      <ul className="mt-3 grid gap-2 text-sm">
        {content.subject_lines.map((subject) => (
          <li className="border border-[var(--border)] px-3 py-2" key={subject}>
            {subject}
          </li>
        ))}
      </ul>
      <p className="mt-4 text-sm text-[var(--muted)]">{content.preview_text}</p>
      <p className="mt-4 whitespace-pre-wrap text-sm leading-6">{content.body}</p>
      <p className="mt-4 text-sm font-medium">{content.cta}</p>
      <CopyButton copied={copiedKey === "newsletter"} onClick={() => onCopy("newsletter", text)} />
    </section>
  );
}

function BlogResults({
  content,
  copiedKey,
  onCopy,
}: {
  content: BlogContent;
  copiedKey: string | null;
  onCopy: (key: string, text: string) => Promise<void>;
}) {
  const text = [
    content.title,
    content.meta_description,
    content.introduction,
    ...content.sections.map((section) => `${section.heading}\n${section.body}`),
    content.conclusion,
  ].join("\n\n");
  return (
    <section className="mt-5 border border-[var(--border)] p-4">
      <h3 className="text-lg font-semibold">{content.title}</h3>
      <p className="mt-2 text-sm text-[var(--muted)]">{content.meta_description}</p>
      <p className="mt-4 text-sm leading-6">{content.introduction}</p>
      <div className="mt-4 grid gap-4">
        {content.sections.map((section) => (
          <div key={section.heading}>
            <h4 className="font-medium">{section.heading}</h4>
            <p className="mt-2 text-sm leading-6">{section.body}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-sm font-medium">{content.conclusion}</p>
      <CopyButton copied={copiedKey === "blog"} onClick={() => onCopy("blog", text)} />
    </section>
  );
}

function ShortsResults({
  content,
  copiedKey,
  onCopy,
}: {
  content: ShortsContent;
  copiedKey: string | null;
  onCopy: (key: string, text: string) => Promise<void>;
}) {
  return (
    <div className="mt-5 grid gap-4">
      {content.clips.map((clip, index) => {
        const text = `${clip.title}\n${clip.start_seconds}s-${clip.end_seconds}s\n${clip.hook}\n\n${clip.script}`;
        return (
          <article className="border border-[var(--border)] p-4" key={`${clip.title}-${index}`}>
            <p className="font-semibold">{clip.title}</p>
            <p className="mt-1 text-sm text-[var(--muted)]">
              {clip.start_seconds}s-{clip.end_seconds}s
            </p>
            <p className="mt-3 text-sm leading-6">{clip.hook}</p>
            <p className="mt-3 text-sm leading-6">{clip.script}</p>
            <CopyButton
              copied={copiedKey === `short-${index}`}
              onClick={() => onCopy(`short-${index}`, text)}
            />
          </article>
        );
      })}
    </div>
  );
}

function CarouselResults({
  content,
  copiedKey,
  onCopy,
}: {
  content: CarouselContent;
  copiedKey: string | null;
  onCopy: (key: string, text: string) => Promise<void>;
}) {
  const text = [
    content.title,
    ...content.slides.map((slide) => `${slide.slide_number}. ${slide.headline}\n${slide.body}`),
    content.caption,
  ].join("\n\n");
  return (
    <section className="mt-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-semibold">{content.title}</h3>
        <CopyButton copied={copiedKey === "carousel"} onClick={() => onCopy("carousel", text)} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {content.slides.map((slide) => (
          <article className="border border-[var(--border)] p-4" key={slide.slide_number}>
            <p className="text-sm text-[var(--muted)]">Slide {slide.slide_number}</p>
            <p className="mt-2 font-medium">{slide.headline}</p>
            <p className="mt-2 text-sm leading-6">{slide.body}</p>
          </article>
        ))}
      </div>
      <p className="mt-4 border border-[var(--border)] p-3 text-sm leading-6">{content.caption}</p>
    </section>
  );
}

function CopyButton({ copied, onClick }: { copied: boolean; onClick: () => void }) {
  return (
    <button
      className="mt-4 border border-[var(--border)] px-3 py-1 text-sm hover:border-[var(--accent)]"
      onClick={onClick}
      type="button"
    >
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function tabClass(isActive: boolean) {
  return [
    "min-h-10 px-3 text-sm font-medium",
    isActive ? "bg-[var(--accent)] text-white" : "bg-white text-[var(--muted)]",
  ].join(" ");
}
