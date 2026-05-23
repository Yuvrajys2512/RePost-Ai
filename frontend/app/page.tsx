"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { supabase } from "../lib/supabase";
import { apiFetch } from "../lib/api";

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
  created_at: string;
};

type UserProfile = {
  id: string;
  email: string;
  plan: string;
  videos_used_this_month: number;
  billing_cycle_start: string;
};

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
  // Auth State
  const [session, setSession] = useState<any>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);

  // App workspace tabs
  const [activeTab, setActiveTab] = useState<"workspace" | "billing" | "history">("workspace");

  // Video processing State
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [transcriptText, setTranscriptText] = useState("");
  const [job, setJob] = useState<JobResponse | null>(null);
  const [pollUrl, setPollUrl] = useState<string | null>(null);
  const [selectedView, setSelectedView] = useState<ContentView>("twitter");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // History state
  const [history, setHistory] = useState<JobResponse[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Billing states
  const [billingLoading, setBillingLoading] = useState(false);
  const [upgradeMessage, setUpgradeMessage] = useState<string | null>(null);
  const [simulatedPlan, setSimulatedPlan] = useState("starter");

  // 1. Subscribe to Authentication state changes
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session: currentSession } }) => {
      setSession(currentSession);
      if (!currentSession) {
        setAuthLoading(false);
      }
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      setSession(currentSession);
      if (!currentSession) {
        setAuthLoading(false);
        setUserProfile(null);
        setHistory([]);
      }
    });

    return () => {
      subscription.unsubscribe();
    };
  }, []);

  // 2. Fetch User Profile and Video History when authenticated
  useEffect(() => {
    if (!session) return;

    fetchUserProfile();
    fetchHistory();
    setAuthLoading(false);
  }, [session]);

  // 3. Monitor checkout redirects and process mock upgrades
  useEffect(() => {
    if (typeof window === "undefined" || !session) return;

    const urlParams = new URLSearchParams(window.location.search);
    const mockUpgrade = urlParams.get("mock-upgrade");
    
    if (mockUpgrade) {
      handleSimulatedUpgrade(mockUpgrade);
      // Clear query params
      const newUrl = window.location.pathname;
      window.history.replaceState({}, document.title, newUrl);
    }
  }, [session]);

  // Fetch helper routines
  async function fetchUserProfile() {
    try {
      const profile = await apiFetch("/api/billing/user");
      setUserProfile(profile);
    } catch (err) {
      console.error("Could not fetch user profile details", err);
    }
  }

  async function fetchHistory() {
    setHistoryLoading(true);
    try {
      const data = await apiFetch("/api/history?page=1&per_page=50");
      setHistory(data.videos || []);
    } catch (err) {
      console.error("Could not fetch history list", err);
    } finally {
      setHistoryLoading(false);
    }
  }

  // Quota enforcement calculation
  const planLimits = useMemo(() => {
    const limits: Record<string, number> = { free: 2, starter: 10, pro: 30, agency: 99999 };
    return limits[userProfile?.plan || "free"] || 2;
  }, [userProfile?.plan]);

  const hasRemainingQuota = useMemo(() => {
    if (!userProfile) return true;
    return userProfile.videos_used_this_month < planLimits;
  }, [userProfile, planLimits]);

  // Polling for processing status
  useEffect(() => {
    if (!pollUrl || job?.status === "completed" || job?.status === "failed") {
      return;
    }

    let cancelled = false;
    const poll = async () => {
      try {
        const nextJob = (await apiFetch(pollUrl)) as JobResponse;
        if (!cancelled) {
          setJob(nextJob);
          setError(nextJob.error);
          if (nextJob.status === "completed") {
            // refresh profile usage and history
            fetchUserProfile();
            fetchHistory();
          }
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

  const canSubmit = useMemo(() => {
    return youtubeUrl.trim().length > 0 && !isSubmitting && hasRemainingQuota;
  }, [isSubmitting, youtubeUrl, hasRemainingQuota]);

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
      const data = (await apiFetch("/api/videos/process", {
        method: "POST",
        json: {
          youtube_url: youtubeUrl,
          platforms: ["twitter", "linkedin", "newsletter", "blog", "shorts", "carousel"],
          transcript_text: transcriptText.trim() || undefined,
        },
      })) as ProcessResponse;

      setPollUrl(data.poll_url);
      setJob({
        job_id: data.job_id,
        status: data.status,
        status_detail: "Queued for transcript extraction",
        progress: 0,
        youtube_url: youtubeUrl,
        content: null,
        error: null,
        created_at: new Date().toISOString(),
      });
      
      // Instantly increment local quota display for responsive feedback
      if (userProfile) {
        setUserProfile({
          ...userProfile,
          videos_used_this_month: userProfile.videos_used_this_month + 1,
        });
      }
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

  // Handle live checkout upgrade redirection
  async function handleUpgrade(plan: string) {
    setBillingLoading(true);
    setUpgradeMessage(null);
    try {
      const data = await apiFetch("/api/billing/checkout", {
        method: "POST",
        json: { plan },
      });
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (err) {
      setUpgradeMessage(err instanceof Error ? err.message : "Checkout generation failed.");
    } finally {
      setBillingLoading(false);
    }
  }

  // Developer simulated upgrade callback
  async function handleSimulatedUpgrade(plan: string) {
    setUpgradeMessage("Processing payment simulation...");
    try {
      const res = await apiFetch("/api/billing/mock-charge", {
        method: "POST",
        json: { plan },
      });
      if (res.status === "success") {
        setUpgradeMessage(`Simulation successful! Upgraded to ${plan.toUpperCase()} tier.`);
        fetchUserProfile();
      }
    } catch (err) {
      setUpgradeMessage("Simulated upgrade failed.");
    }
  }

  // Auth logout routine
  async function handleLogout() {
    await supabase.auth.signOut();
  }

  // 4. Auth loading skeleton
  if (authLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[var(--background)] text-[var(--foreground)]">
        <div className="flex flex-col items-center gap-4">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-[var(--accent)] border-t-transparent" />
          <p className="text-sm font-medium text-[var(--muted)]">Loading creator workspace...</p>
        </div>
      </div>
    );
  }

  // 5. Landing page for unauthenticated visitors
  if (!session) {
    return (
      <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)]">
        {/* Navigation */}
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold bg-gradient-to-r from-[var(--accent)] to-[var(--accent-strong)] bg-clip-text text-transparent">
              RePost AI
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="text-sm font-medium hover:text-[var(--accent)]">
              Sign In
            </Link>
            <Link
              href="/auth/signup"
              className="bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--accent-strong)] shadow-md"
            >
              Get Started Free
            </Link>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="mx-auto max-w-4xl px-6 py-20 text-center">
          <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-3 py-1 uppercase tracking-wider">
            Next-Gen Content Repurposing Agent
          </span>
          <h1 className="mt-6 text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
            Repurpose YouTube Videos Into <br />
            <span className="bg-gradient-to-r from-[var(--accent)] to-[var(--accent-strong)] bg-clip-text text-transparent">
              Ready-to-Publish
            </span>{" "}
            Social Campaigns
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-[var(--muted)] leading-8">
            Stop summary generators. RePost AI deconstructs the emotional hook, narrative arc, and insights of your videos to compile premium content for Twitter, LinkedIn, Newsletters, Blogs, Shorts scripts, and Instagram carousels in seconds.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link
              href="/auth/signup"
              className="bg-[var(--accent)] px-6 py-3.5 text-base font-semibold text-white hover:bg-[var(--accent-strong)] shadow-lg hover:shadow-xl transition-all"
            >
              Start Repurposing Free
            </Link>
            <a
              href="#pricing"
              className="border border-[var(--border)] bg-white px-6 py-3.5 text-base font-semibold text-[var(--muted)] hover:text-black hover:border-black transition-all"
            >
              View Pricing
            </a>
          </div>
        </section>

        {/* Pricing Cards */}
        <section id="pricing" className="mx-auto max-w-6xl px-6 py-20 border-t border-[var(--border)]">
          <div className="text-center">
            <h2 className="text-3xl font-bold tracking-tight">Flexible plans for every creator</h2>
            <p className="mt-2 text-base text-[var(--muted)]">
              All plans include the complete platform expansion agent. Upgrading unlocks more generations.
            </p>
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {/* Free */}
            <div className="flex flex-col justify-between border border-[var(--border)] bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
              <div>
                <h3 className="text-lg font-bold">Free Plan</h3>
                <p className="mt-2 text-sm text-[var(--muted)]">Test the repurposing intelligence</p>
                <p className="mt-4 text-3xl font-extrabold">$0</p>
                <ul className="mt-6 space-y-3 text-sm">
                  <li className="flex items-center gap-2">✓ 2 Video conversions / month</li>
                  <li className="flex items-center gap-2">✓ Access all 6 platforms</li>
                  <li className="flex items-center gap-2">✓ Smart Narrative Analyzer</li>
                </ul>
              </div>
              <Link
                href="/auth/signup"
                className="mt-8 block w-full bg-[var(--background)] py-2 text-center text-sm font-semibold text-[var(--foreground)] hover:bg-[var(--border)]"
              >
                Sign Up Free
              </Link>
            </div>

            {/* Starter */}
            <div className="flex flex-col justify-between border border-[var(--border)] bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
              <div>
                <h3 className="text-lg font-bold text-[var(--accent)]">Starter Plan</h3>
                <p className="mt-2 text-sm text-[var(--muted)]">Perfect for active creators</p>
                <p className="mt-4 text-3xl font-extrabold">$19</p>
                <p className="text-xs text-[var(--muted)]">per month</p>
                <ul className="mt-6 space-y-3 text-sm">
                  <li className="flex items-center gap-2">✓ 10 Video conversions / month</li>
                  <li className="flex items-center gap-2">✓ Access all 6 platforms</li>
                  <li className="flex items-center gap-2">✓ Advanced voice profile matching</li>
                </ul>
              </div>
              <Link
                href="/auth/signup"
                className="mt-8 block w-full bg-[var(--accent)] py-2 text-center text-sm font-semibold text-white hover:bg-[var(--accent-strong)]"
              >
                Get Started
              </Link>
            </div>

            {/* Pro */}
            <div className="flex flex-col justify-between border border-[var(--accent)] bg-white p-6 shadow-md relative">
              <span className="absolute top-0 right-6 -translate-y-1/2 bg-[var(--accent)] text-white text-xs px-2.5 py-0.5 font-semibold">
                MOST POPULAR
              </span>
              <div>
                <h3 className="text-lg font-bold">Pro Plan</h3>
                <p className="mt-2 text-sm text-[var(--muted)]">For content machines</p>
                <p className="mt-4 text-3xl font-extrabold">$29</p>
                <p className="text-xs text-[var(--muted)]">per month</p>
                <ul className="mt-6 space-y-3 text-sm">
                  <li className="flex items-center gap-2">✓ 30 Video conversions / month</li>
                  <li className="flex items-center gap-2">✓ Access all 6 platforms</li>
                  <li className="flex items-center gap-2">✓ Multi-voice matching profiles</li>
                </ul>
              </div>
              <Link
                href="/auth/signup"
                className="mt-8 block w-full bg-[var(--accent)] py-2 text-center text-sm font-semibold text-white hover:bg-[var(--accent-strong)]"
              >
                Get Started
              </Link>
            </div>

            {/* Agency */}
            <div className="flex flex-col justify-between border border-[var(--border)] bg-white p-6 shadow-sm hover:shadow-md transition-shadow">
              <div>
                <h3 className="text-lg font-bold">Agency Plan</h3>
                <p className="mt-2 text-sm text-[var(--muted)]">Unlimited content scales</p>
                <p className="mt-4 text-3xl font-extrabold">$49</p>
                <p className="text-xs text-[var(--muted)]">per month</p>
                <ul className="mt-6 space-y-3 text-sm">
                  <li className="flex items-center gap-2">✓ Unlimited video runs</li>
                  <li className="flex items-center gap-2">✓ Unlimited voice profiles</li>
                  <li className="flex items-center gap-2">✓ Shared team workspace access</li>
                </ul>
              </div>
              <Link
                href="/auth/signup"
                className="mt-8 block w-full bg-[var(--background)] py-2 text-center text-sm font-semibold text-[var(--foreground)] hover:bg-[var(--border)]"
              >
                Get Started
              </Link>
            </div>
          </div>
        </section>
      </main>
    );
  }

  // 6. Logged-in Dashboard Workspace Panel
  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)] px-4 py-6 sm:px-6">
      <section className="mx-auto flex max-w-6xl flex-col gap-6">
        
        {/* Navigation Sidebar/Header */}
        <header className="flex flex-col gap-4 border-b border-[var(--border)] pb-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <span className="text-xl font-bold bg-gradient-to-r from-[var(--accent)] to-[var(--accent-strong)] bg-clip-text text-transparent">
                RePost AI
              </span>
              <span className="border border-[var(--accent)] px-2 py-0.5 text-xs font-semibold uppercase text-[var(--accent)] rounded bg-emerald-50">
                {userProfile?.plan || "free"} Plan
              </span>
            </div>
            <p className="text-sm text-[var(--muted)] mt-1">{session.user.email}</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => setActiveTab("workspace")}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === "workspace"
                  ? "bg-[var(--accent)] text-white"
                  : "bg-white text-[var(--muted)] border border-[var(--border)] hover:bg-slate-50"
              }`}
            >
              Workspace
            </button>
            <button
              onClick={() => setActiveTab("billing")}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === "billing"
                  ? "bg-[var(--accent)] text-white"
                  : "bg-white text-[var(--muted)] border border-[var(--border)] hover:bg-slate-50"
              }`}
            >
              Billing & Quotas
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === "history"
                  ? "bg-[var(--accent)] text-white"
                  : "bg-white text-[var(--muted)] border border-[var(--border)] hover:bg-slate-50"
              }`}
            >
              History ({history.length})
            </button>
            <button
              onClick={handleLogout}
              className="border border-[var(--danger)] bg-[var(--danger-soft)] px-4 py-2 text-sm font-medium text-[var(--danger)] hover:bg-rose-100 transition-colors ml-4"
            >
              Logout
            </button>
          </div>
        </header>

        {/* Global Tab Enforcements */}
        
        {/* VIEW 1: Repurposing Workspace */}
        {activeTab === "workspace" && (
          <section className="grid gap-5 lg:grid-cols-[0.95fr_1.35fr]">
            
            {/* Input Workspace */}
            <div className="border border-[var(--border)] bg-[var(--panel)] p-5 flex flex-col justify-between min-h-[460px]">
              <form onSubmit={handleSubmit}>
                <div className="flex justify-between items-center mb-4">
                  <label className="text-sm font-medium" htmlFor="youtube-url">
                    YouTube URL
                  </label>
                  
                  {/* Local Quota Indicator */}
                  <span className="text-xs text-[var(--muted)]">
                    Usage: <strong className="text-black">{userProfile?.videos_used_this_month || 0}</strong> / {planLimits} runs
                  </span>
                </div>

                <input
                  id="youtube-url"
                  className="min-h-11 w-full border border-[var(--border)] bg-white px-3 outline-none focus:border-[var(--accent)] text-sm"
                  onChange={(event) => setYoutubeUrl(event.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  type="url"
                  value={youtubeUrl}
                  disabled={!hasRemainingQuota || isSubmitting}
                />

                <label className="mt-5 block text-sm font-medium" htmlFor="transcript-text">
                  Transcript override (Optional)
                </label>
                <textarea
                  id="transcript-text"
                  className="mt-2 min-h-36 w-full resize-y border border-[var(--border)] bg-white px-3 py-2 outline-none focus:border-[var(--accent)] text-sm"
                  onChange={(event) => setTranscriptText(event.target.value)}
                  placeholder="Insert custom transcript for testing / prompt verification."
                  value={transcriptText}
                  disabled={!hasRemainingQuota || isSubmitting}
                />

                {!hasRemainingQuota ? (
                  <div className="mt-4 border border-[var(--danger)] bg-[var(--danger-soft)] px-3 py-3 text-sm text-[var(--danger)] flex flex-col gap-2">
                    <p className="font-semibold">Quota Limit Reached!</p>
                    <p className="text-xs">You have processed {userProfile?.videos_used_this_month} / {planLimits} videos this month. Upgrade in the Billing tab to continue.</p>
                  </div>
                ) : null}

                <button
                  className="mt-5 min-h-11 w-full bg-[var(--accent)] px-5 font-semibold text-white hover:bg-[var(--accent-strong)] disabled:cursor-not-allowed disabled:bg-[var(--disabled)] shadow-md"
                  disabled={!canSubmit}
                  type="submit"
                >
                  {isSubmitting ? "Dispatching conversion..." : "Generate Content Kit"}
                </button>

                {error ? (
                  <p className="mt-4 border border-[var(--danger)] bg-[var(--danger-soft)] px-3 py-2 text-sm text-[var(--danger)]">
                    {error}
                  </p>
                ) : null}
              </form>

              {/* Minimal Quota usage bar */}
              <div className="mt-8 border-t border-[var(--border)] pt-4">
                <div className="flex justify-between text-xs text-[var(--muted)] mb-1.5">
                  <span>Current billing cycle usage</span>
                  <span>{Math.min(100, Math.round(((userProfile?.videos_used_this_month || 0) / planLimits) * 100))}%</span>
                </div>
                <div className="h-2 w-full bg-[var(--track)] rounded-full overflow-hidden">
                  <div
                    className="h-2 bg-[var(--accent)] transition-all duration-300"
                    style={{ width: `${Math.min(100, ((userProfile?.videos_used_this_month || 0) / planLimits) * 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Results / Status Workspace */}
            <section className="border border-[var(--border)] bg-[var(--panel)] p-5 min-h-[460px]">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between border-b border-[var(--border)] pb-4">
                <div>
                  <h2 className="text-lg font-semibold">Active conversions</h2>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {job?.status_detail ?? "Awaiting a YouTube video URL..."}
                  </p>
                </div>
                <span className="w-fit border border-[var(--border)] px-3 py-1 text-xs font-semibold capitalize text-[var(--muted)] bg-slate-50">
                  {job?.status ?? "idle"}
                </span>
              </div>

              <div className="mt-5 h-2.5 w-full bg-[var(--track)] overflow-hidden rounded-full">
                <div
                  className="h-2.5 bg-[var(--accent)] transition-all duration-500 rounded-full"
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
                <div className="mt-8 grid gap-4 sm:grid-cols-3">
                  {[
                    { step: "Extracting Transcript", active: job?.progress ? job.progress >= 25 : false },
                    { step: "Deconstructing Arc", active: job?.progress ? job.progress >= 55 : false },
                    { step: "Platform Composition", active: job?.progress ? job.progress >= 85 : false },
                  ].map((item, index) => (
                    <div
                      className={`border px-3 py-5 transition-colors ${
                        item.active
                          ? "border-[var(--accent)] bg-emerald-50 text-[var(--accent-strong)]"
                          : job?.status === "failed"
                          ? "border-red-200 bg-red-50 text-red-700"
                          : "border-[var(--border)] text-[var(--muted)] bg-white"
                      }`}
                      key={index}
                    >
                      <p className="text-sm font-semibold">{item.step}</p>
                      <p className="mt-2 text-xs">
                        {job?.status === "failed"
                          ? "Interrupted"
                          : item.active
                          ? "Complete"
                          : job?.status === "processing" && job.progress < (index * 30 + 25)
                          ? "In Progress"
                          : "Pending"}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </section>
        )}

        {/* VIEW 2: Billing & Quotas Dashboard */}
        {activeTab === "billing" && (
          <section className="border border-[var(--border)] bg-[var(--panel)] p-6">
            <h2 className="text-2xl font-bold tracking-tight">Billing & Quota Management</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              View your monthly conversion quotas, manage subscriptions, and configure active plans.
            </p>

            {upgradeMessage && (
              <div className="mt-4 border border-[var(--accent)] bg-emerald-50 px-4 py-3 text-sm font-semibold text-[var(--accent-strong)]">
                {upgradeMessage}
              </div>
            )}

            {/* Quota overview */}
            <div className="mt-8 grid gap-5 md:grid-cols-3 border-b border-[var(--border)] pb-8">
              <div className="border border-[var(--border)] p-4 bg-slate-50">
                <p className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">Active tier</p>
                <p className="mt-2 text-2xl font-bold capitalize text-[var(--accent)]">{userProfile?.plan || "free"}</p>
              </div>

              <div className="border border-[var(--border)] p-4 bg-slate-50 col-span-2">
                <div className="flex justify-between items-center">
                  <p className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">Monthly run quota</p>
                  <span className="text-sm font-bold text-black">
                    {userProfile?.videos_used_this_month || 0} / {planLimits} converted
                  </span>
                </div>
                <div className="mt-4 h-3 w-full bg-[var(--track)] rounded-full overflow-hidden">
                  <div
                    className="h-3 bg-[var(--accent)] transition-all duration-300 rounded-full"
                    style={{ width: `${Math.min(100, ((userProfile?.videos_used_this_month || 0) / planLimits) * 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Subscriptions upgrade grid */}
            <div className="mt-8">
              <h3 className="text-lg font-bold mb-5">Change or upgrade your subscription plan</h3>
              <div className="grid gap-6 md:grid-cols-3">
                {[
                  {
                    name: "Starter",
                    price: "$19",
                    desc: "Perfect for growing creators",
                    features: ["10 video runs / month", "Access all 6 platforms", "Style attributes injector"],
                    active: userProfile?.plan === "starter",
                  },
                  {
                    name: "Pro",
                    price: "$29",
                    desc: "Built for active content generators",
                    features: ["30 video runs / month", "Access all 6 platforms", "Unlimited voice profile match"],
                    active: userProfile?.plan === "pro",
                  },
                  {
                    name: "Agency",
                    price: "$49",
                    desc: "Uncapped scaling potential",
                    features: ["Unlimited video runs", "Access all 6 platforms", "Shared agency seat controls"],
                    active: userProfile?.plan === "agency",
                  },
                ].map((item) => (
                  <div
                    key={item.name}
                    className={`border p-5 flex flex-col justify-between bg-white relative ${
                      item.active ? "border-[var(--accent)] ring-2 ring-[var(--accent)]/10 shadow-md" : "border-[var(--border)] shadow-sm"
                    }`}
                  >
                    {item.active && (
                      <span className="absolute top-0 right-4 -translate-y-1/2 bg-[var(--accent)] text-white text-[10px] font-bold px-2 py-0.5 uppercase tracking-wider">
                        Active Plan
                      </span>
                    )}
                    <div>
                      <h4 className="font-bold text-lg">{item.name} Plan</h4>
                      <p className="mt-1 text-xs text-[var(--muted)]">{item.desc}</p>
                      <div className="mt-4 flex items-baseline gap-1">
                        <span className="text-3xl font-extrabold">{item.price}</span>
                        <span className="text-xs text-[var(--muted)]">/ month</span>
                      </div>
                      <ul className="mt-5 space-y-2.5 text-xs text-[var(--muted)]">
                        {item.features.map((f) => (
                          <li key={f}>✓ {f}</li>
                        ))}
                      </ul>
                    </div>

                    <button
                      onClick={() => handleUpgrade(item.name)}
                      disabled={item.active || billingLoading}
                      className={`mt-6 w-full py-2 text-xs font-semibold text-center transition-all ${
                        item.active
                          ? "bg-slate-100 text-slate-500 cursor-default"
                          : "bg-[var(--accent)] text-white hover:bg-[var(--accent-strong)] shadow"
                      }`}
                    >
                      {item.active ? "Current Tier" : billingLoading ? "Requesting..." : `Subscribe to ${item.name}`}
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* DEVELOPER SIMULATOR ACTIONS */}
            <div className="mt-10 border border-amber-200 bg-amber-50/50 p-5">
              <h4 className="text-sm font-bold text-amber-900 flex items-center gap-1.5">
                ⚡ Developer Sandbox Panel
              </h4>
              <p className="text-xs text-amber-800 mt-1">
                Skip webhooks and checkout overlays in local dev. Use this simulation console to instantly force-toggle active plan variants on the Postgres user record.
              </p>
              
              <div className="mt-4 flex flex-wrap items-center gap-3">
                <select
                  value={simulatedPlan}
                  onChange={(e) => setSimulatedPlan(e.target.value)}
                  className="bg-white border border-amber-300 text-xs px-3 py-1.5 outline-none rounded"
                >
                  <option value="free">Free Plan (2 runs)</option>
                  <option value="starter">Starter Plan ($19 - 10 runs)</option>
                  <option value="pro">Pro Plan ($29 - 30 runs)</option>
                  <option value="agency">Agency Plan ($49 - Unlimited)</option>
                </select>
                
                <button
                  onClick={() => handleSimulatedUpgrade(simulatedPlan)}
                  className="bg-amber-600 text-white text-xs font-bold px-4 py-2 hover:bg-amber-700 transition-colors shadow"
                >
                  Simulate Account Upgrade
                </button>
              </div>
            </div>
          </section>
        )}

        {/* VIEW 3: Conversions History Log */}
        {activeTab === "history" && (
          <section className="border border-[var(--border)] bg-[var(--panel)] p-6 min-h-[460px]">
            <h2 className="text-2xl font-bold tracking-tight">Video Conversions History</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Browse previous runs, review generated copy kits, and reload past workspaces.
            </p>

            {historyLoading ? (
              <div className="flex justify-center items-center py-20">
                <div className="h-6 w-6 animate-spin rounded-full border-3 border-[var(--accent)] border-t-transparent" />
              </div>
            ) : history.length === 0 ? (
              <div className="text-center py-20 border border-dashed border-[var(--border)] mt-6">
                <p className="text-sm text-[var(--muted)] font-medium">No video campaigns generated yet.</p>
                <button
                  onClick={() => setActiveTab("workspace")}
                  className="mt-4 bg-[var(--accent)] text-white text-xs font-semibold px-4 py-2 hover:bg-[var(--accent-strong)]"
                >
                  Process First Video
                </button>
              </div>
            ) : (
              <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {history.map((item) => (
                  <article
                    key={item.job_id}
                    className="border border-[var(--border)] p-4 flex flex-col justify-between bg-white hover:border-slate-400 transition-colors"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted)]">
                          {new Date(item.created_at).toLocaleDateString(undefined, {
                            month: "short",
                            day: "numeric",
                            year: "numeric",
                          })}
                        </span>
                        <span
                          className={`text-[10px] font-semibold px-2 py-0.5 rounded capitalize ${
                            item.status === "completed"
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : item.status === "failed"
                              ? "bg-rose-50 text-rose-700 border border-rose-200"
                              : "bg-amber-50 text-amber-700 border border-amber-200"
                          }`}
                        >
                          {item.status}
                        </span>
                      </div>

                      <h4 className="mt-3 font-semibold text-sm line-clamp-2 text-[var(--foreground)]">
                        {item.youtube_url}
                      </h4>
                      
                      <p className="text-xs text-[var(--muted)] mt-1 line-clamp-1">
                        ID: {item.job_id}
                      </p>

                      {item.content && (
                        <div className="mt-4 flex flex-wrap gap-1">
                          {Object.keys(item.content).map((platform) => (
                            <span
                              key={platform}
                              className="text-[9px] bg-slate-100 text-slate-600 px-1.5 py-0.5 uppercase tracking-wide border border-slate-200 font-semibold"
                            >
                              {platform}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => {
                        setJob(item);
                        setPollUrl(null);
                        setActiveTab("workspace");
                      }}
                      className="mt-5 w-full bg-[var(--background)] py-1.5 text-center text-xs font-semibold hover:bg-[var(--border)] border border-[var(--border)] transition-colors"
                    >
                      Load in Workspace
                    </button>
                  </article>
                ))}
              </div>
            )}
          </section>
        )}
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
          <h3 className="font-semibold text-sm">Standalone tweets</h3>
        </div>
        <div className="mt-3 grid gap-3">
          {content.twitter.standalone_tweets.map((tweet, index) => (
            <article className="border border-[var(--border)] p-3 bg-white" key={`${tweet.text}-${index}`}>
              <p className="text-xs leading-6">{tweet.text}</p>
              <button
                className="mt-3 border border-[var(--border)] px-3 py-1 text-[11px] font-semibold hover:border-[var(--accent)] bg-slate-50 transition-colors"
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
          <h3 className="font-semibold text-sm">Thread</h3>
          <button
            className="border border-[var(--border)] px-3 py-1 text-[11px] font-semibold hover:border-[var(--accent)] bg-slate-50 transition-colors"
            onClick={() => onCopy("thread", threadText)}
            type="button"
          >
            {copiedKey === "thread" ? "Copied" : "Copy all"}
          </button>
        </div>
        <ol className="mt-3 grid gap-3">
          {content.twitter.thread.map((tweet, index) => (
            <li className="border border-[var(--border)] p-3 text-xs leading-6 bg-white" key={index}>
              <span className="mr-2 text-[var(--muted)] font-bold">{index + 1}.</span>
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
          <article className="border border-[var(--border)] p-4 bg-white" key={`${post.hook}-${index}`}>
            <p className="font-semibold text-xs text-black">{post.hook}</p>
            <p className="mt-3 whitespace-pre-wrap text-xs leading-6 text-slate-700">{post.body}</p>
            <p className="mt-3 text-xs font-semibold text-[var(--accent)]">{post.cta}</p>
            <button
              className="mt-4 border border-[var(--border)] px-3 py-1 text-[11px] font-semibold hover:border-[var(--accent)] bg-slate-50 transition-colors"
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
    <section className="mt-5 border border-[var(--border)] p-4 bg-white">
      <h3 className="font-semibold text-sm">Newsletter draft</h3>
      <ul className="mt-3 grid gap-2 text-xs">
        {content.subject_lines.map((subject) => (
          <li className="border border-[var(--border)] px-3 py-2 bg-slate-50" key={subject}>
            <strong>Subject Idea:</strong> {subject}
          </li>
        ))}
      </ul>
      <p className="mt-4 text-xs text-[var(--muted)] font-medium">Preview: {content.preview_text}</p>
      <p className="mt-4 whitespace-pre-wrap text-xs leading-6 text-slate-700">{content.body}</p>
      <p className="mt-4 text-xs font-semibold text-[var(--accent)]">{content.cta}</p>
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
    <section className="mt-5 border border-[var(--border)] p-4 bg-white">
      <h3 className="text-base font-bold text-black">{content.title}</h3>
      <p className="mt-2 text-xs text-[var(--muted)] font-semibold">SEO Meta: {content.meta_description}</p>
      <p className="mt-4 text-xs leading-6 text-slate-700">{content.introduction}</p>
      <div className="mt-4 grid gap-4">
        {content.sections.map((section) => (
          <div key={section.heading} className="border-t border-slate-100 pt-3">
            <h4 className="font-semibold text-xs text-black">{section.heading}</h4>
            <p className="mt-2 text-xs leading-6 text-slate-700">{section.body}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs font-semibold text-black border-t border-slate-100 pt-3">{content.conclusion}</p>
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
          <article className="border border-[var(--border)] p-4 bg-white flex flex-col justify-between" key={`${clip.title}-${index}`}>
            <div>
              <p className="font-semibold text-xs text-black">{clip.title}</p>
              <p className="mt-1 text-[10px] text-[var(--accent)] font-bold">
                Timestamps: {clip.start_seconds}s-{clip.end_seconds}s
              </p>
              <p className="mt-3 text-xs leading-6 text-slate-800 italic"><strong>Hook:</strong> {clip.hook}</p>
              <p className="mt-3 text-xs leading-6 text-slate-600 whitespace-pre-wrap"><strong>Script:</strong> {clip.script}</p>
            </div>
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
      <div className="flex items-center justify-between gap-3 bg-white border border-[var(--border)] p-3">
        <h3 className="font-semibold text-xs text-black">{content.title}</h3>
        <CopyButton copied={copiedKey === "carousel"} onClick={() => onCopy("carousel", text)} />
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {content.slides.map((slide) => (
          <article className="border border-[var(--border)] p-4 bg-white" key={slide.slide_number}>
            <p className="text-[10px] text-[var(--accent)] font-bold uppercase tracking-wider">Slide {slide.slide_number}</p>
            <p className="mt-2 font-semibold text-xs text-black">{slide.headline}</p>
            <p className="mt-2 text-xs leading-6 text-slate-600">{slide.body}</p>
          </article>
        ))}
      </div>
      <p className="mt-4 border border-[var(--border)] p-4 text-xs leading-6 bg-white text-slate-700">
        <strong>Instagram Caption:</strong> <br />
        <span className="block mt-2 whitespace-pre-wrap">{content.caption}</span>
      </p>
    </section>
  );
}

function CopyButton({ copied, onClick }: { copied: boolean; onClick: () => void }) {
  return (
    <button
      className="mt-4 border border-[var(--border)] px-4 py-1.5 text-xs font-semibold hover:border-[var(--accent)] bg-slate-50 transition-colors"
      onClick={onClick}
      type="button"
    >
      {copied ? "Copied Copy" : "Copy to Clipboard"}
    </button>
  );
}

function tabClass(isActive: boolean) {
  return [
    "min-h-11 px-3 text-xs font-semibold transition-colors",
    isActive ? "bg-[var(--accent)] text-white shadow-inner" : "bg-white text-[var(--muted)] hover:bg-slate-50",
  ].join(" ");
}
