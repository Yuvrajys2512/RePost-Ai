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
  const [activeTab, setActiveTab] = useState<"workspace" | "billing" | "history" | "analytics" | "calendar">("workspace");

  // Analytics states
  const [analyticsData, setAnalyticsData] = useState<any>(null);
  const [analyticsLoading, setAnalyticsLoading] = useState(false);

  // API Key management states
  const [apiKeys, setApiKeys] = useState<any[]>([]);
  const [apiKeyName, setApiKeyName] = useState("");
  const [creatingKey, setCreatingKey] = useState(false);
  const [keysLoading, setKeysLoading] = useState(false);

  // Calendar states
  const [selectedCalendarCampaign, setSelectedCalendarCampaign] = useState<any>(null);
  const [selectedCalendarPlatform, setSelectedCalendarPlatform] = useState<string | null>(null);

  // Video processing State
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [transcriptText, setTranscriptText] = useState("");
  const [job, setJob] = useState<JobResponse | null>(null);
  const [pollUrl, setPollUrl] = useState<string | null>(null);
  const [selectedView, setSelectedView] = useState<ContentView>("twitter");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  // Fetch analytics helper
  async function fetchAnalytics() {
    setAnalyticsLoading(true);
    try {
      const data = await apiFetch("/api/analytics");
      setAnalyticsData(data);
    } catch (err) {
      console.error("Could not fetch analytics data", err);
    } finally {
      setAnalyticsLoading(false);
    }
  }

  // Fetch developer API keys
  async function fetchApiKeys() {
    if (userProfile?.plan !== "agency") return;
    setKeysLoading(true);
    try {
      const keys = await apiFetch("/api/billing/keys");
      setApiKeys(keys);
    } catch (err) {
      console.error("Could not fetch API keys", err);
    } finally {
      setKeysLoading(false);
    }
  }

  // Create Developer API Key
  async function handleCreateApiKey(e: FormEvent) {
    e.preventDefault();
    if (!apiKeyName.trim() || creatingKey) return;
    setCreatingKey(true);
    try {
      const res = await apiFetch("/api/billing/keys", {
        method: "POST",
        json: { name: apiKeyName.trim() },
      });
      if (res.status === "success") {
        setToastMessage("Developer API Key created successfully!");
        setApiKeyName("");
        fetchApiKeys();
      }
    } catch (err) {
      setToastMessage("Could not create API key.");
    } finally {
      setCreatingKey(false);
    }
  }

  // Revoke Developer API Key
  async function handleRevokeApiKey(keyId: string) {
    if (!confirm("Are you sure you want to revoke this API Key? Programmatic requests using it will fail immediately.")) return;
    try {
      const res = await apiFetch(`/api/billing/keys/${keyId}`, {
        method: "DELETE",
      });
      if (res.status === "success") {
        setToastMessage("API key revoked successfully.");
        fetchApiKeys();
      }
    } catch (err) {
      setToastMessage("Could not revoke API key.");
    }
  }

  // Trigger loading analytics when tab is selected
  useEffect(() => {
    if (activeTab === "analytics") {
      fetchAnalytics();
    }
  }, [activeTab]);

  // Trigger loading API keys on billing tab when user has agency plan
  useEffect(() => {
    if (activeTab === "billing" && userProfile?.plan === "agency") {
      fetchApiKeys();
    }
  }, [activeTab, userProfile?.plan]);

  // Calendar weeks builder helper
  const calendarWeeks = useMemo(() => {
    const today = new Date();
    const dayOfWeek = today.getDay(); // 0 is Sunday, 1 is Monday
    // Calculate Monday of this week
    const mondayDiff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek;
    const monday = new Date(today);
    monday.setDate(today.getDate() + mondayDiff);

    const weekDays = [];
    const dayNames = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    for (let i = 0; i < 7; i++) {
      const d = new Date(monday);
      d.setDate(monday.getDate() + i);
      weekDays.push({
        name: dayNames[i],
        date: d,
        dateString: d.toLocaleDateString(),
        formattedDate: d.toLocaleDateString(undefined, { month: "short", day: "numeric" }),
      });
    }
    return weekDays;
  }, []);

  function renderCalendarPlatformCopy(content: any, platform: string): string {
    if (!content || !content[platform]) return "No content generated";
    const data = content[platform];

    switch (platform) {
      case "twitter":
        const standalones = data.standalone_tweets.map((t: any, i: number) => `Tweet Option ${i + 1}:\n${t.text}`).join("\n\n");
        const thread = data.thread.map((t: any, i: number) => `${i + 1}. ${t.text}`).join("\n\n");
        return `=== STANDALONE TWEETS ===\n\n${standalones}\n\n=== ENGAGEMENT THREAD ===\n\n${thread}`;
      case "linkedin":
        return data.posts.map((p: any, i: number) => `Post Option ${i + 1}:\nHook: ${p.hook}\n\n${p.body}\n\nCTA: ${p.cta}`).join("\n\n---\n\n");
      case "newsletter":
        return `Subject options:\n${data.subject_lines.join(" | ")}\nPreview: ${data.preview_text}\n\n${data.body}\n\nCTA: ${data.cta}`;
      case "blog":
        const sections = data.sections.map((s: any) => `H2: ${s.heading}\n${s.body}`).join("\n\n");
        return `Title: ${data.title}\nSEO Meta: ${data.meta_description}\n\n${data.introduction}\n\n${sections}\n\nConclusion: ${data.conclusion}`;
      case "shorts":
        return data.clips.map((c: any, i: number) => `Short Clip ${i + 1} (${c.start_seconds}s - ${c.end_seconds}s):\nHook: ${c.hook}\nScript:\n${c.script}`).join("\n\n---\n\n");
      case "carousel":
        const slides = data.slides.map((s: any) => `Slide ${s.slide_number} [${s.headline}]:\n${s.body}`).join("\n\n");
        return `Carousel Title: ${data.title}\n\n${slides}\n\nCaption outline:\n${data.caption}`;
      default:
        return JSON.stringify(data, null, 2);
    }
  }


  // Exporter / Toast notification state
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Regeneration loading state in UI
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Interactive Onboarding Walkthrough Steps (1 to 4, null if closed)
  const [onboardingStep, setOnboardingStep] = useState<number | null>(null);

  // History state
  const [history, setHistory] = useState<JobResponse[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  // Billing states
  const [billingLoading, setBillingLoading] = useState(false);
  const [upgradeMessage, setUpgradeMessage] = useState<string | null>(null);
  const [simulatedPlan, setSimulatedPlan] = useState("starter");

  // FAQ Accordion expanded state
  const [expandedFaq, setExpandedFaq] = useState<number | null>(null);

  // Testimonials state
  const [activeTestimonial, setActiveTestimonial] = useState(0);

  // Youtube URL live validation
  const isValidUrl = useMemo(() => {
    if (!youtubeUrl) return true; // Empty is neutral
    const regex = /^(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})/;
    return regex.test(youtubeUrl);
  }, [youtubeUrl]);

  // Toast auto-dismissal
  useEffect(() => {
    if (toastMessage) {
      const timer = window.setTimeout(() => setToastMessage(null), 3000);
      return () => window.clearTimeout(timer);
    }
  }, [toastMessage]);

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

    // Auto-trigger onboarding walkthrough overlay for new users
    const hasSeenTour = localStorage.getItem("repost_has_seen_tour");
    if (!hasSeenTour) {
      setOnboardingStep(1);
    }
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
            fetchUserProfile();
            fetchHistory();
            setToastMessage("Campaign content kit generated successfully!");
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
    return youtubeUrl.trim().length > 0 && isValidUrl && !isSubmitting && hasRemainingQuota;
  }, [isSubmitting, youtubeUrl, isValidUrl, hasRemainingQuota]);

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

  async function copyText(key: string, text: string, platform?: string, contentId?: string) {
    await navigator.clipboard.writeText(text);
    setCopiedKey(key);
    window.setTimeout(() => setCopiedKey(null), 1400);

    if (contentId && platform) {
      try {
        await apiFetch(`/api/content/${contentId}/track`, {
          method: "POST",
          json: { action: "content_copied", platform },
        });
      } catch (err) {
        console.error("Could not track copy event", err);
      }
    }
  }

  // Handle single platform regeneration UI triggers
  async function handleRegeneratePlatform() {
    if (!job || isRegenerating) return;

    setIsRegenerating(true);
    setToastMessage(`Regenerating ${selectedView.toUpperCase()} copy...`);
    try {
      const res = await apiFetch(`/api/videos/${job.job_id}/regenerate`, {
        method: "POST",
        json: { platform: selectedView },
      });

      if (res.status === "success" && job.content) {
        const updatedContent = {
          ...job.content,
          [selectedView]: res.payload,
        };

        setJob({
          ...job,
          content: updatedContent,
        });
        setToastMessage(`Refreshed ${selectedView.toUpperCase()} copy kit in place!`);
      }
    } catch (err) {
      setToastMessage("Regeneration failed. Using fallback copy.");
    } finally {
      setIsRegenerating(false);
    }
  }

  // Copy Entire Kit exporter
  async function handleCopyEntireKit() {
    if (!job || !job.content) return;

    // Track export analytics for all platforms in this campaign
    if (job.content_ids) {
      for (const [platform, contentId] of Object.entries(job.content_ids)) {
        try {
          await apiFetch(`/api/content/${contentId}/track`, {
            method: "POST",
            json: { action: "content_copied", platform },
          });
        } catch (err) {
          console.error("Could not track copy event for platform", platform, err);
        }
      }
    }

    const kit = job.content;
    let formattedText = `=== REPOST AI CAMPAIGN KIT ===\nVideo URL: ${job.youtube_url}\n\n`;

    // 1. Twitter
    if (kit.twitter) {
      formattedText += `--- TWITTER STANDALONE TWEETS ---\n`;
      kit.twitter.standalone_tweets.forEach((t, i) => {
        formattedText += `Tweet ${i + 1}:\n${t.text}\n\n`;
      });
      formattedText += `--- TWITTER THREAD ---\n`;
      kit.twitter.thread.forEach((t, i) => {
        formattedText += `${i + 1}. ${t.text}\n\n`;
      });
    }

    // 2. LinkedIn
    if (kit.linkedin) {
      formattedText += `--- LINKEDIN POSTS ---\n`;
      kit.linkedin.posts.forEach((p, i) => {
        formattedText += `Post ${i + 1}:\n${p.hook}\n\n${p.body}\n\n${p.cta}\n\n`;
      });
    }

    // 3. Newsletter
    if (kit.newsletter) {
      formattedText += `--- NEWSLETTER DRAFT ---\nSubject Lines: ${kit.newsletter.subject_lines.join(" | ")}\nPreview: ${kit.newsletter.preview_text}\n\n${kit.newsletter.body}\n\n${kit.newsletter.cta}\n\n`;
    }

    // 4. Blog
    if (kit.blog) {
      formattedText += `--- SEO BLOG POST ---\nTitle: ${kit.blog.title}\nSEO Meta: ${kit.blog.meta_description}\n\n${kit.blog.introduction}\n\n`;
      kit.blog.sections.forEach((s) => {
        formattedText += `H2: ${s.heading}\n${s.body}\n\n`;
      });
      formattedText += `Conclusion:\n${kit.blog.conclusion}\n\n`;
    }

    // 5. Shorts
    if (kit.shorts) {
      formattedText += `--- SHORTS VIDEO SCRIPTS ---\n`;
      kit.shorts.clips.forEach((c) => {
        formattedText += `Clip Title: ${c.title} (${c.start_seconds}s - ${c.end_seconds}s)\nHook: ${c.hook}\nScript: ${c.script}\n\n`;
      });
    }

    // 6. Carousel
    if (kit.carousel) {
      formattedText += `--- INSTAGRAM CAROUSEL ---\nTitle: ${kit.carousel.title}\n`;
      kit.carousel.slides.forEach((s) => {
        formattedText += `Slide ${s.slide_number} [${s.headline}]:\n${s.body}\n\n`;
      });
      formattedText += `Caption:\n${kit.carousel.caption}\n\n`;
    }

    await navigator.clipboard.writeText(formattedText);
    setToastMessage("Entire content kit copied to clipboard!");
  }

  // Download Markdown Campaign Exporter
  async function handleDownloadMarkdown() {
    if (!job || !job.content) return;

    // Track export analytics for all platforms in this campaign
    if (job.content_ids) {
      for (const [platform, contentId] of Object.entries(job.content_ids)) {
        try {
          await apiFetch(`/api/content/${contentId}/track`, {
            method: "POST",
            json: { action: "content_exported", platform },
          });
        } catch (err) {
          console.error("Could not track export event for platform", platform, err);
        }
      }
    }

    const kit = job.content;
    let md = `# RePost AI Content Campaign Kit\n\n- **Source Video URL:** ${job.youtube_url}\n- **Date Compiled:** ${new Date(job.created_at).toLocaleDateString()}\n\n---\n\n`;

    // 1. Twitter
    if (kit.twitter) {
      md += `## 🐦 Twitter/X Campaign\n\n### Standalone Copy Options\n\n`;
      kit.twitter.standalone_tweets.forEach((t, i) => {
        md += `> **Option ${i + 1}**\n> ${t.text}\n\n`;
      });
      md += `### Engagement Value Thread\n\n`;
      kit.twitter.thread.forEach((t, i) => {
        md += `${i + 1}. ${t.text}\n\n`;
      });
      md += `---\n\n`;
    }

    // 2. LinkedIn
    if (kit.linkedin) {
      md += `## 💼 LinkedIn Campaign\n\n`;
      kit.linkedin.posts.forEach((p, i) => {
        md += `### Post Outline ${i + 1}\n\n**Hook:** ${p.hook}\n\n**Body:**\n${p.body}\n\n**Call-To-Action:** *${p.cta}*\n\n---\n\n`;
      });
    }

    // 3. Newsletter
    if (kit.newsletter) {
      md += `## 📧 Newsletter Draft\n\n- **Subject Line Options:**\n`;
      kit.newsletter.subject_lines.forEach((s) => {
        md += `  - ${s}\n`;
      });
      md += `- **Preview Text:** *${kit.newsletter.preview_text}*\n\n${kit.newsletter.body}\n\n**CTA Link:** [${kit.newsletter.cta}](${job.youtube_url})\n\n---\n\n`;
    }

    // 4. Blog
    if (kit.blog) {
      md += `## 📝 SEO Optimized Blog Post\n\n# ${kit.blog.title}\n\n*Meta Description: ${kit.blog.meta_description}*\n\n${kit.blog.introduction}\n\n`;
      kit.blog.sections.forEach((s) => {
        md += `## ${s.heading}\n\n${s.body}\n\n`;
      });
      md += `### Conclusion\n\n${kit.blog.conclusion}\n\n---\n\n`;
    }

    // 5. Shorts
    if (kit.shorts) {
      md += `## 🎥 YouTube Shorts & Reels Scripts\n\n`;
      kit.shorts.clips.forEach((c, i) => {
        md += `### Clip ${i + 1}: ${c.title}\n- **Timestamps:** ${c.start_seconds}s - ${c.end_seconds}s\n- **Hook Beat:** ${c.hook}\n\n**Narrative Script:**\n${c.script}\n\n---\n\n`;
      });
    }

    // 6. Carousel
    if (kit.carousel) {
      md += `## 📸 Instagram Carousel Outline\n\n# ${kit.carousel.title}\n\n`;
      kit.carousel.slides.forEach((s) => {
        md += `### Slide ${s.slide_number}\n**Headline:** ${s.headline}\n**Body Text:** ${s.body}\n\n`;
      });
      md += `### Caption Copy\n\`\`\`text\n${kit.carousel.caption}\n\`\`\`\n`;
    }

    const blob = new Blob([md], { type: "text/markdown;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `repost_campaign_${job.job_id.slice(0, 8)}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setToastMessage("Markdown campaign file downloaded successfully!");
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

  // Onboarding walkthrough controls
  function handleNextOnboarding() {
    if (onboardingStep === null) return;
    if (onboardingStep < 4) {
      setOnboardingStep(onboardingStep + 1);
    } else {
      setOnboardingStep(null);
      localStorage.setItem("repost_has_seen_tour", "true");
      setToastMessage("Onboarding tour complete! Enjoy repurposing.");
    }
  }

  function handleSkipOnboarding() {
    setOnboardingStep(null);
    localStorage.setItem("repost_has_seen_tour", "true");
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
      <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)] scroll-smooth">
        {/* Navigation */}
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5 border-b border-[var(--border)]">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold bg-gradient-to-r from-[var(--accent)] to-[var(--accent-strong)] bg-clip-text text-transparent">
              RePost AI
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="text-sm font-semibold hover:text-[var(--accent)] transition-colors">
              Sign In
            </Link>
            <Link
              href="/auth/signup"
              className="bg-[var(--accent)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--accent-strong)] shadow-md transition-all hover:scale-[1.02]"
            >
              Get Started Free
            </Link>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="mx-auto max-w-4xl px-6 py-20 text-center">
          <span className="bg-emerald-100 text-emerald-800 text-xs font-semibold px-3 py-1 uppercase tracking-wider rounded-full shadow-sm">
            ✨ Complete Creator Repurposing Toolkit
          </span>
          <h1 className="mt-8 text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl">
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
              className="bg-[var(--accent)] px-6 py-3.5 text-base font-semibold text-white hover:bg-[var(--accent-strong)] shadow-lg hover:shadow-xl transition-all hover:scale-[1.03]"
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

        {/* Testimonials Carousel Section */}
        <section className="mx-auto max-w-5xl px-6 py-12 border-t border-[var(--border)]">
          <div className="text-center">
            <h2 className="text-2xl font-bold tracking-tight">Trusted by creator machines</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">See how 100K+ creators multiply their reach</p>
          </div>

          <div className="mt-8 bg-white border border-[var(--border)] p-8 shadow-sm relative overflow-hidden">
            {[
              {
                quote: "RePost AI completely changed my editing cycle. It used to take me 2 days to draft posts, newsletter outlines, and blogs for my videos. Now I just copy and adjust in 2 minutes.",
                author: "Devin Allen",
                subscribers: "142K Subscribers",
                niche: "Tech & Coding",
              },
              {
                quote: "The LinkedIn posts generated by RePost actually sound organic and drive major comments. It hooks readers exactly the way I did in the video, rather than sounding like normal chatgpt trash.",
                author: "Sarah Jenkins",
                subscribers: "450K Subscribers",
                niche: "Startup & Marketing",
              },
              {
                quote: "Timestamps matching scripts for Shorts is amazing. Our editing team instantly pulls 3-5 vertical clips from my long-form uploads using the calculated timestamps in RePost.",
                author: "Marcus Stone",
                subscribers: "88K Subscribers",
                niche: "Fitness & Lifestyle",
              },
            ].map((t, i) => (
              <div
                key={i}
                className={`transition-opacity duration-300 ${
                  activeTestimonial === i ? "block" : "hidden"
                }`}
              >
                <p className="text-base italic leading-7 text-[var(--foreground)]">"{t.quote}"</p>
                <div className="mt-6 flex items-center justify-between">
                  <div>
                    <p className="font-bold text-sm text-black">{t.author}</p>
                    <p className="text-xs text-[var(--muted)]">{t.subscribers} • {t.niche}</p>
                  </div>
                  <div className="flex gap-1.5">
                    {[0, 1, 2].map((dot) => (
                      <button
                        key={dot}
                        onClick={() => setActiveTestimonial(dot)}
                        className={`h-2.5 w-2.5 rounded-full ${
                          activeTestimonial === dot ? "bg-[var(--accent)]" : "bg-slate-200"
                        }`}
                      />
                    ))}
                  </div>
                </div>
              </div>
            ))}
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

        {/* FAQs Section */}
        <section className="mx-auto max-w-4xl px-6 py-20 border-t border-[var(--border)]">
          <div className="text-center mb-10">
            <h2 className="text-3xl font-bold tracking-tight">Frequently Asked Questions</h2>
            <p className="mt-2 text-base text-[var(--muted)]">Everything you need to know about RePost AI</p>
          </div>

          <div className="space-y-4">
            {[
              {
                q: "How does RePost AI learn my unique brand voice?",
                a: "In your Voice Profile settings, you paste 3 to 10 samples of your best past newsletter issues, tweets, or blog drafts. Our analyzer node extracts stylistic features (sentence pacing, emoticon counts, vocabulary complexity) and feeds it directly as a context schema into all generator models.",
              },
              {
                q: "What happens if a video has disabled or missing auto-captions?",
                a: "If our default fast API extractors encounter a video without captions, we trigger a helpful fallback notice. You can instantly copy-paste any transcript text directly into the 'Transcript override' box in your workspace to complete the conversion.",
              },
              {
                q: "How does the monthly quota cycle reset?",
                a: "Each account runs on a 30-day billing cycle. At the end of each cycle, your processed counter resets to zero automatically. If you run out of runs early, you can instantly upgrade plan tiers via the Billing tab.",
              },
            ].map((faq, index) => (
              <div className="border border-[var(--border)] bg-white" key={index}>
                <button
                  onClick={() => setExpandedFaq(expandedFaq === index ? null : index)}
                  className="flex w-full items-center justify-between p-5 text-left font-semibold text-sm text-black"
                >
                  <span>{faq.q}</span>
                  <span className="text-lg font-bold">{expandedFaq === index ? "−" : "+"}</span>
                </button>
                {expandedFaq === index && (
                  <div className="p-5 border-t border-[var(--border)] text-xs leading-6 text-[var(--muted)]">
                    {faq.a}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      </main>
    );
  }

  // 6. Logged-in Dashboard Workspace Panel
  return (
    <main className="min-h-screen bg-[var(--background)] text-[var(--foreground)] px-4 py-6 sm:px-6 relative">
      
      {/* Dynamic Toast Notifications */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-[#1e293b] text-white text-xs px-4 py-3 shadow-xl flex items-center gap-2 border border-slate-700 animate-slide-in">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          {toastMessage}
        </div>
      )}

      {/* Interactive Onboarding Walkthrough Overlays */}
      {onboardingStep !== null && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border-2 border-[var(--accent)] p-6 max-w-md w-full shadow-2xl relative">
            <span className="absolute top-4 right-4 text-xs font-bold text-[var(--accent)]">
              Step {onboardingStep} of 4
            </span>
            
            {onboardingStep === 1 && (
              <div>
                <h4 className="text-base font-bold text-black flex items-center gap-1">📺 YouTube URL Input</h4>
                <p className="text-xs text-[var(--muted)] leading-5 mt-2">
                  Paste your YouTube video link in the URL field. RePost AI will automatically extract the auto-captions to feed into the AI agent.
                </p>
              </div>
            )}
            
            {onboardingStep === 2 && (
              <div>
                <h4 className="text-base font-bold text-black flex items-center gap-1">📝 Transcript Overrides</h4>
                <p className="text-xs text-[var(--muted)] leading-5 mt-2">
                  If captions are disabled on the video, no worries! Just paste the script or transcript text in the optional text area override box.
                </p>
              </div>
            )}

            {onboardingStep === 3 && (
              <div>
                <h4 className="text-base font-bold text-black flex items-center gap-1">⚙️ Social Campaign Workspace</h4>
                <p className="text-xs text-[var(--muted)] leading-5 mt-2">
                  Watch the agent progression in real-time. Toggle Twitter Standalones, Threads, LinkedIn hooks, Blogs, and Carousel slides, and download them cleanly.
                </p>
              </div>
            )}

            {onboardingStep === 4 && (
              <div>
                <h4 className="text-base font-bold text-black flex items-center gap-1">💳 Billing Quota & Simulator</h4>
                <p className="text-xs text-[var(--muted)] leading-5 mt-2">
                  Monitor your monthly conversions. Use the **Developer Sandbox Simulator** in the Billing tab to test Starlette webhook plan updates with one click!
                </p>
              </div>
            )}

            <div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4">
              <button
                onClick={handleSkipOnboarding}
                className="text-xs text-[var(--muted)] hover:text-black font-semibold"
              >
                Skip Tutorial
              </button>
              
              <button
                onClick={handleNextOnboarding}
                className="bg-[var(--accent)] text-white text-xs font-semibold px-4 py-2 hover:bg-[var(--accent-strong)]"
              >
                {onboardingStep < 4 ? "Next Step" : "Get Started"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Container */}
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

          <div className="flex flex-wrap items-center gap-2">
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
              onClick={() => setActiveTab("analytics")}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === "analytics"
                  ? "bg-[var(--accent)] text-white"
                  : "bg-white text-[var(--muted)] border border-[var(--border)] hover:bg-slate-50"
              }`}
            >
              Analytics Dashboard
            </button>
            <button
              onClick={() => setActiveTab("calendar")}
              className={`px-4 py-2 text-sm font-medium ${
                activeTab === "calendar"
                  ? "bg-[var(--accent)] text-white"
                  : "bg-white text-[var(--muted)] border border-[var(--border)] hover:bg-slate-50"
              }`}
            >
              Content Calendar
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
              onClick={() => setOnboardingStep(1)}
              className="bg-slate-100 hover:bg-slate-200 border border-[var(--border)] text-black px-4 py-2 text-sm font-medium"
            >
              Tour Tour
            </button>
            <button
              onClick={handleLogout}
              className="border border-[var(--danger)] bg-[var(--danger-soft)] px-4 py-2 text-sm font-medium text-[var(--danger)] hover:bg-rose-100 transition-colors ml-4"
            >
              Logout
            </button>
          </div>
        </header>

        {/* VIEW 1: Repurposing Workspace */}
        {activeTab === "workspace" && (
          <section className="grid gap-5 lg:grid-cols-[0.95fr_1.35fr]">
            
            {/* Input Workspace */}
            <div className="border border-[var(--border)] bg-[var(--panel)] p-5 flex flex-col justify-between min-h-[460px] relative">
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
                  className={`min-h-11 w-full border px-3 outline-none text-sm transition-colors ${
                    !isValidUrl
                      ? "border-[var(--danger)] bg-rose-50/20 focus:border-[var(--danger)]"
                      : "border-[var(--border)] bg-white focus:border-[var(--accent)]"
                  }`}
                  onChange={(event) => setYoutubeUrl(event.target.value)}
                  placeholder="https://www.youtube.com/watch?v=..."
                  type="url"
                  value={youtubeUrl}
                  disabled={!hasRemainingQuota || isSubmitting}
                />
                
                {!isValidUrl && (
                  <p className="text-[11px] text-[var(--danger)] font-semibold mt-1.5">
                    ⚠ Please paste a valid YouTube video or Shorts link structure
                  </p>
                )}

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
            <div className="border border-[var(--border)] bg-[var(--panel)] p-5 min-h-[460px] flex flex-col justify-between">
              <div>
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

                {/* Friendly Caption Failure Display */}
                {job?.status === "failed" && (job.error?.toLowerCase().includes("transcript") || job.status_detail.includes("transcript")) ? (
                  <div className="mt-6 border border-amber-300 bg-amber-50 p-5 text-amber-900 rounded">
                    <h4 className="text-sm font-bold flex items-center gap-1.5">⚡ Video Captions Unavailable</h4>
                    <p className="text-xs mt-2 leading-5">
                      This YouTube video does not contain public auto-captions, preventing the pipeline from analyzing it.
                    </p>
                    <div className="mt-4 border-l-2 border-amber-500 pl-3">
                      <p className="text-[11px] font-semibold">Easy Resolution:</p>
                      <p className="text-[11px] mt-1">
                        1. Copy the script or transcript text of the video.
                        <br />
                        2. Paste it in the **"Transcript override"** box to the left.
                        <br />
                        3. Re-click **"Generate Content Kit"** to process the conversion kit.
                      </p>
                    </div>
                  </div>
                ) : null}

                {job?.content && (
                  <ContentResults
                    content={job.content}
                    contentIds={job.content_ids || null}
                    copiedKey={copiedKey}
                    onCopy={copyText}
                    selectedView={selectedView}
                    setSelectedView={setSelectedView}
                    isRegenerating={isRegenerating}
                    onRegenerate={handleRegeneratePlatform}
                  />
                )}

                {/* Pendings list if no active conversions */}
                {!job?.content && job?.status !== "failed" && (
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
                            : "border-[var(--border)] text-[var(--muted)] bg-white"
                        }`}
                        key={index}
                      >
                        <p className="text-sm font-semibold">{item.step}</p>
                        <p className="mt-2 text-xs">
                          {item.active
                            ? "Complete"
                            : job?.status === "processing" && job.progress < (index * 30 + 25)
                            ? "In Progress"
                            : "Pending"}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Action Campaign exporters in Workspace Card footer */}
              {job?.content && (
                <div className="mt-6 pt-4 border-t border-[var(--border)] flex flex-wrap gap-3 items-center justify-end">
                  <button
                    onClick={handleCopyEntireKit}
                    className="border border-slate-300 bg-white hover:bg-slate-50 px-4 py-2 text-xs font-semibold shadow-sm transition-colors"
                  >
                    📋 Copy Entire Kit
                  </button>
                  <button
                    onClick={handleDownloadMarkdown}
                    className="bg-[var(--accent)] text-white hover:bg-[var(--accent-strong)] px-4 py-2 text-xs font-bold shadow-md transition-colors"
                  >
                    💾 Download Markdown (.md)
                  </button>
                </div>
              )}
            </div>
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

            {/* API ACCESS KEYS PANEL */}
            <div className="mt-10 border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-6">
                <div>
                  <h3 className="text-lg font-bold text-black flex items-center gap-1.5">
                    🔑 Developer API Integration
                  </h3>
                  <p className="text-xs text-[var(--muted)]">
                    Process YouTube video campaigns programmatically using our REST endpoints.
                  </p>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 uppercase tracking-wider bg-emerald-50 text-[var(--accent)] border border-[var(--accent)]">
                  Agency Tier Only
                </span>
              </div>

              {userProfile?.plan !== "agency" ? (
                <div className="border border-dashed border-slate-200 p-8 text-center bg-slate-50/50">
                  <p className="text-sm font-semibold text-slate-700">Developer API Keys are locked</p>
                  <p className="text-xs text-[var(--muted)] mt-1.5 max-w-md mx-auto">
                    API keys permit automated, header-authenticated programmatic conversions gated exclusively for high-scale users. Upgrade to the **Agency Tier** to generate credentials.
                  </p>
                  <button
                    onClick={() => handleUpgrade("Agency")}
                    className="mt-4 bg-[var(--accent)] text-white text-xs font-semibold px-4 py-2 hover:bg-[var(--accent-strong)] shadow"
                  >
                    Upgrade to Agency Tier
                  </button>
                </div>
              ) : (
                <div>
                  <form onSubmit={handleCreateApiKey} className="flex gap-3 mb-6">
                    <input
                      type="text"
                      placeholder="e.g. Production Webhook Integration"
                      value={apiKeyName}
                      onChange={(e) => setApiKeyName(e.target.value)}
                      className="flex-1 bg-white border border-[var(--border)] text-xs px-3 py-2 outline-none focus:border-[var(--accent)]"
                      required
                    />
                    <button
                      type="submit"
                      disabled={creatingKey || !apiKeyName.trim()}
                      className="bg-[var(--accent)] text-white text-xs font-bold px-4 py-2 hover:bg-[var(--accent-strong)] disabled:bg-slate-200 disabled:text-slate-400 shadow"
                    >
                      {creatingKey ? "Creating..." : "Generate API Key"}
                    </button>
                  </form>

                  {keysLoading ? (
                    <div className="flex justify-center items-center py-6">
                      <div className="h-5 w-5 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent" />
                    </div>
                  ) : apiKeys.length === 0 ? (
                    <p className="text-xs text-[var(--muted)] italic text-center py-4 bg-slate-50">No API keys created yet. Generate one above!</p>
                  ) : (
                    <div className="border border-slate-100 overflow-hidden">
                      <table className="w-full text-left text-xs border-collapse">
                        <thead>
                          <tr className="bg-slate-50 border-b border-slate-100">
                            <th className="p-3 font-semibold text-slate-700">Key Name</th>
                            <th className="p-3 font-semibold text-slate-700">Token Credential</th>
                            <th className="p-3 font-semibold text-slate-700">Created At</th>
                            <th className="p-3 font-semibold text-slate-700 text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100">
                          {apiKeys.map((key) => (
                            <tr key={key.id} className="hover:bg-slate-50/50">
                              <td className="p-3 font-semibold text-black">{key.name}</td>
                              <td className="p-3 font-mono text-slate-600 bg-slate-50 select-all">{key.key_value}</td>
                              <td className="p-3 text-slate-500">
                                {new Date(key.created_at).toLocaleDateString()}
                              </td>
                              <td className="p-3 text-right">
                                <button
                                  onClick={() => handleRevokeApiKey(key.id)}
                                  className="text-[10px] font-bold text-[var(--danger)] hover:underline"
                                >
                                  Revoke Key
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
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

        {/* VIEW 4: Analytics Dashboard */}
        {activeTab === "analytics" && (
          <section className="border border-[var(--border)] bg-[var(--panel)] p-6 min-h-[460px]">
            <div className="border-b border-[var(--border)] pb-4 mb-6">
              <h2 className="text-2xl font-bold tracking-tight">Campaign Telemetry & Analytics</h2>
              <p className="mt-1 text-sm text-[var(--muted)]">
                Inspect aggregated platform usage, clipboard telemetry, and active publication volumes.
              </p>
            </div>

            {analyticsLoading ? (
              <div className="flex justify-center items-center py-20">
                <div className="h-6 w-6 animate-spin rounded-full border-3 border-[var(--accent)] border-t-transparent" />
              </div>
            ) : !analyticsData ? (
              <p className="text-xs text-[var(--muted)] italic text-center py-10">No analytics data available yet.</p>
            ) : (
              <div className="grid gap-6">
                {/* Statistics Cards */}
                <div className="grid gap-5 md:grid-cols-2">
                  <div className="border border-slate-200 bg-white p-5 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">Total Campaigns Converted</p>
                    <p className="mt-3 text-4xl font-extrabold text-black">{analyticsData.total_runs}</p>
                    <p className="mt-2 text-xs text-[var(--muted)]">Calculated from total processed long-form video jobs</p>
                  </div>
                  <div className="border border-slate-200 bg-white p-5 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-wider text-[var(--muted)]">Platform Copy Distribution</p>
                    <p className="mt-3 text-4xl font-extrabold text-[var(--accent)]">
                      {Object.values(analyticsData.platform_distribution).reduce((a: any, b: any) => a + b, 0) as number} copies
                    </p>
                    <p className="mt-2 text-xs text-[var(--muted)]">Sum of clipboard exports logged across social channels</p>
                  </div>
                </div>

                {/* Progress bars representing platforms */}
                <div className="border border-slate-200 bg-white p-5 shadow-sm">
                  <h3 className="text-sm font-bold text-black mb-4">Channels Share Metrics</h3>
                  <div className="grid gap-4">
                    {["twitter", "linkedin", "newsletter", "blog", "shorts", "carousel"].map((platform) => {
                      const count = analyticsData.platform_distribution[platform] || 0;
                      const total = Object.values(analyticsData.platform_distribution).reduce((a: any, b: any) => a + b, 0) as number || 1;
                      const percentage = Math.round((count / total) * 100);
                      
                      const colors: Record<string, string> = {
                        twitter: "bg-slate-900",
                        linkedin: "bg-blue-600",
                        newsletter: "bg-purple-600",
                        blog: "bg-amber-500",
                        shorts: "bg-rose-500",
                        carousel: "bg-pink-500"
                      };

                      return (
                        <div key={platform} className="grid grid-cols-[80px_1fr_40px] items-center gap-3">
                          <span className="text-xs font-bold uppercase text-slate-700">{platform}</span>
                          <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={`h-3 rounded-full ${colors[platform] || "bg-[var(--accent)]"} transition-all duration-500`}
                              style={{ width: `${percentage}%` }}
                            />
                          </div>
                          <span className="text-right text-xs font-semibold text-slate-800">{count}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Recent activity timeline */}
                <div className="border border-slate-200 bg-white p-5 shadow-sm">
                  <h3 className="text-sm font-bold text-black mb-4">Audited Event Telemetry</h3>
                  {analyticsData.recent_activity.length === 0 ? (
                    <p className="text-xs text-[var(--muted)] italic">No recent copying telemetry captured yet.</p>
                  ) : (
                    <div className="divide-y divide-slate-100">
                      {analyticsData.recent_activity.map((log: any) => (
                        <div key={log.id} className="py-2.5 flex items-center justify-between text-xs">
                          <div className="flex items-center gap-2">
                            <span className={`h-2 w-2 rounded-full ${log.action.includes("export") ? "bg-purple-400" : "bg-emerald-400"}`} />
                            <span className="font-semibold text-slate-800">
                              {log.action === "content_copied" ? "Copied" : "Exported"} <strong className="uppercase">{log.platform}</strong> campaign outline
                            </span>
                          </div>
                          <span className="text-slate-400 font-medium">
                            {new Date(log.created_at).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}
                          </span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </section>
        )}

        {/* VIEW 5: Content Calendar */}
        {activeTab === "calendar" && (
          <section className="border border-[var(--border)] bg-[var(--panel)] p-6 min-h-[460px]">
            <div className="border-b border-[var(--border)] pb-4 mb-6">
              <h2 className="text-2xl font-bold tracking-tight">Creator Content Calendar</h2>
              <p className="mt-1 text-sm text-[var(--muted)]">
                Schedule, formats inspect, and schedule publication outlines dynamically for the active weekly slot.
              </p>
            </div>

            <div className="grid gap-4 xl:grid-cols-7 lg:grid-cols-4 md:grid-cols-2 sm:grid-cols-1">
              {calendarWeeks.map((day) => {
                // Find completed campaigns matching this day
                const campaignsOnDay = history.filter((item) => {
                  if (item.status !== "completed") return false;
                  const itemDate = new Date(item.created_at).toLocaleDateString();
                  return itemDate === day.dateString;
                });

                return (
                  <div key={day.name} className="border border-slate-200 bg-white p-4 min-h-[200px] flex flex-col justify-between hover:shadow-xs transition-shadow">
                    <div>
                      <div className="flex justify-between items-baseline border-b border-slate-100 pb-2 mb-3">
                        <span className="text-xs font-extrabold text-black uppercase">{day.name}</span>
                        <span className="text-[10px] text-slate-400 font-bold">{day.formattedDate}</span>
                      </div>

                      {campaignsOnDay.length === 0 ? (
                        <p className="text-[10px] text-slate-400 italic">No campaigns scheduled</p>
                      ) : (
                        <div className="grid gap-2">
                          {campaignsOnDay.map((camp) => (
                            <div key={camp.job_id} className="border border-emerald-100 bg-emerald-50/50 p-2 text-[10px] rounded hover:border-[var(--accent)] transition-all">
                              <p className="font-bold text-slate-850 truncate mb-1.5" title={camp.youtube_url}>
                                🔗 {camp.youtube_url.split("v=")[1] || "Video"}
                              </p>
                              
                              <div className="grid gap-1">
                                {camp.content && Object.keys(camp.content).map((platform) => (
                                  <button
                                    key={platform}
                                    onClick={() => {
                                      setSelectedCalendarCampaign(camp);
                                      setSelectedCalendarPlatform(platform);
                                    }}
                                    className="w-full text-left bg-white border border-slate-200 hover:border-[var(--accent)] p-1 text-[9px] font-semibold text-slate-700 truncate rounded flex items-center justify-between"
                                  >
                                    <span className="uppercase">{platform}</span>
                                    <span className="text-[8px] text-[var(--accent)]">view →</span>
                                  </button>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Modal for viewing calendar content card */}
            {selectedCalendarCampaign && selectedCalendarPlatform && (
              <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
                <div className="bg-white border border-slate-200 p-6 max-w-2xl w-full shadow-2xl relative flex flex-col justify-between max-h-[85vh]">
                  <div>
                    <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
                      <div>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Scheduled Campaign Preview</span>
                        <h4 className="text-base font-extrabold text-black uppercase mt-1">
                          {selectedCalendarPlatform} Copy Outlines
                        </h4>
                      </div>
                      <button
                        onClick={() => {
                          setSelectedCalendarCampaign(null);
                          setSelectedCalendarPlatform(null);
                        }}
                        className="text-lg font-bold text-slate-400 hover:text-black"
                      >
                        ✕
                      </button>
                    </div>

                    <div className="overflow-y-auto max-h-[50vh] pr-2">
                      <p className="text-[10px] text-slate-550 font-mono mb-4 truncate">
                        Source Video: {selectedCalendarCampaign.youtube_url}
                      </p>
                      
                      <div className="bg-slate-50 p-4 border border-slate-200 text-xs text-slate-700 whitespace-pre-wrap leading-relaxed select-all">
                        {renderCalendarPlatformCopy(selectedCalendarCampaign.content, selectedCalendarPlatform)}
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-slate-100 flex justify-end gap-3">
                    <button
                      onClick={() => {
                        const copyTxt = renderCalendarPlatformCopy(selectedCalendarCampaign.content, selectedCalendarPlatform);
                        navigator.clipboard.writeText(copyTxt);
                        setToastMessage(`${selectedCalendarPlatform.toUpperCase()} copy copied to clipboard!`);
                      }}
                      className="bg-[var(--accent)] text-white hover:bg-[var(--accent-strong)] px-4 py-2 text-xs font-bold shadow-md transition-colors"
                    >
                      📋 Copy to Clipboard
                    </button>
                    <button
                      onClick={() => {
                        setSelectedCalendarCampaign(null);
                        setSelectedCalendarPlatform(null);
                      }}
                      className="border border-slate-300 hover:bg-slate-50 px-4 py-2 text-xs font-semibold shadow-sm transition-colors text-black"
                    >
                      Close Preview
                    </button>
                  </div>
                </div>
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
  contentIds,
  copiedKey,
  onCopy,
  selectedView,
  setSelectedView,
  isRegenerating,
  onRegenerate,
}: {
  content: ContentKit;
  contentIds: Record<string, string> | null;
  copiedKey: string | null;
  onCopy: (key: string, text: string, platform?: string, contentId?: string) => Promise<void>;
  selectedView: ContentView;
  setSelectedView: (view: ContentView) => void;
  isRegenerating: boolean;
  onRegenerate: () => void;
}) {
  const [variations, setVariations] = useState<string[]>([]);
  const [loadingVariations, setLoadingVariations] = useState(false);
  const [showVariations, setShowVariations] = useState(false);
  const [variationsError, setVariationsError] = useState<string | null>(null);

  useEffect(() => {
    setVariations([]);
    setShowVariations(false);
    setVariationsError(null);
  }, [selectedView]);

  async function fetchVariations() {
    const contentId = contentIds?.[selectedView];
    if (!contentId) {
      setVariationsError("No content piece ID found for variations generation.");
      return;
    }
    setLoadingVariations(true);
    setVariationsError(null);
    try {
      const res = await apiFetch(`/api/content/${contentId}/variations`, {
        method: "POST"
      });
      setVariations(res.variations || []);
    } catch (err) {
      setVariationsError("Could not retrieve hook variations.");
    } finally {
      setLoadingVariations(false);
    }
  }

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

      <div className="relative min-h-[100px]">
        {/* Spin loader overlay inside active Platform Result tab during regeneration */}
        {isRegenerating && (
          <div className="absolute inset-0 bg-white/60 backdrop-blur-[1px] z-10 flex flex-col items-center justify-center gap-2">
            <div className="h-6 w-6 animate-spin rounded-full border-3 border-[var(--accent)] border-t-transparent" />
            <p className="text-[10px] font-bold uppercase text-[var(--accent)] tracking-wider">Regenerating tab copy...</p>
          </div>
        )}

        {selectedView === "twitter" && (
          <TwitterResults content={content} copiedKey={copiedKey} onCopy={(key, text) => onCopy(key, text, "twitter", contentIds?.["twitter"])} />
        )}
        {selectedView === "linkedin" && (
          <LinkedInResults content={content} copiedKey={copiedKey} onCopy={(key, text) => onCopy(key, text, "linkedin", contentIds?.["linkedin"])} />
        )}
        {selectedView === "newsletter" && (
          <NewsletterResults content={content.newsletter} copiedKey={copiedKey} onCopy={(key, text) => onCopy(key, text, "newsletter", contentIds?.["newsletter"])} />
        )}
        {selectedView === "blog" && (
          <BlogResults content={content.blog} copiedKey={copiedKey} onCopy={(key, text) => onCopy(key, text, "blog", contentIds?.["blog"])} />
        )}
        {selectedView === "shorts" && (
          <ShortsResults content={content.shorts} copiedKey={copiedKey} onCopy={(key, text) => onCopy(key, text, "shorts", contentIds?.["shorts"])} />
        )}
        {selectedView === "carousel" && (
          <CarouselResults content={content.carousel} copiedKey={copiedKey} onCopy={(key, text) => onCopy(key, text, "carousel", contentIds?.["carousel"])} />
        )}
      </div>

      {/* A/B variations generator drawer */}
      <div className="mt-6 border border-slate-200 bg-slate-50/50 p-4">
        <div className="flex items-center justify-between">
          <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
            🎯 Platform Hook & Headline Variations (A/B Test)
          </h4>
          <button
            onClick={() => {
              const nextShow = !showVariations;
              setShowVariations(nextShow);
              if (nextShow && variations.length === 0) {
                fetchVariations();
              }
            }}
            className="text-xs font-bold text-[var(--accent)] hover:text-[var(--accent-strong)]"
          >
            {showVariations ? "Hide Variations" : "Reveal A/B Hooks"}
          </button>
        </div>

        {showVariations && (
          <div className="mt-4 pt-4 border-t border-slate-200">
            {loadingVariations ? (
              <div className="flex items-center justify-center py-4">
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--accent)] border-t-transparent mr-2" />
                <span className="text-xs text-[var(--muted)]">Generating alternative angles...</span>
              </div>
            ) : variationsError ? (
              <p className="text-xs text-[var(--danger)]">{variationsError}</p>
            ) : (
              <div className="grid gap-3">
                {variations.map((v, i) => (
                  <div key={i} className="bg-white border border-slate-100 p-3 shadow-xs relative group">
                    <span className="absolute top-2.5 right-3 text-[10px] font-bold text-slate-400 uppercase">
                      Angle {String.fromCharCode(65 + i)}
                    </span>
                    <p className="text-xs text-slate-700 leading-relaxed pr-16">{v}</p>
                    <button
                      onClick={() => onCopy(`var-${selectedView}-${i}`, v, selectedView, contentIds?.[selectedView])}
                      className="mt-2.5 text-[10px] font-semibold text-[var(--accent)] hover:text-[var(--accent-strong)] animate-fade-in"
                    >
                      {copiedKey === `var-${selectedView}-${i}` ? "✓ Copied!" : "📋 Copy Angle"}
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Regeneration action button directly under active view results card */}
      <div className="mt-4 flex justify-end">
        <button
          onClick={onRegenerate}
          disabled={isRegenerating}
          className="text-xs font-semibold text-[var(--accent)] hover:text-[var(--accent-strong)] hover:underline flex items-center gap-1 bg-transparent border-0 outline-none"
        >
          🔄 Regenerate {selectedView.toUpperCase()} Copy
        </button>
      </div>
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
      {copied ? "Copied" : "Copy to Clipboard"}
    </button>
  );
}

function tabClass(isActive: boolean) {
  return [
    "min-h-11 px-3 text-xs font-semibold transition-colors",
    isActive ? "bg-[var(--accent)] text-white shadow-inner" : "bg-white text-[var(--muted)] hover:bg-slate-50",
  ].join(" ");
}
