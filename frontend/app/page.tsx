const platforms = ["Twitter/X", "LinkedIn", "Newsletter", "Blog"];

export default function Home() {
  return (
    <main className="min-h-screen px-6 py-8">
      <section className="mx-auto flex max-w-5xl flex-col gap-8">
        <header className="flex items-center justify-between border-b border-[var(--border)] pb-5">
          <div>
            <p className="text-sm font-medium uppercase tracking-[0.12em] text-[var(--accent)]">
              RePost AI
            </p>
            <h1 className="mt-2 text-3xl font-semibold">Content repurposing workspace</h1>
          </div>
          <div className="rounded border border-[var(--border)] bg-white px-3 py-2 text-sm text-[var(--muted)]">
            Phase 0
          </div>
        </header>

        <section className="grid gap-5 md:grid-cols-[1.2fr_0.8fr]">
          <form className="rounded border border-[var(--border)] bg-[var(--panel)] p-5">
            <label className="text-sm font-medium" htmlFor="youtube-url">
              YouTube URL
            </label>
            <div className="mt-3 flex flex-col gap-3 sm:flex-row">
              <input
                id="youtube-url"
                className="min-h-11 flex-1 rounded border border-[var(--border)] px-3 outline-none focus:border-[var(--accent)]"
                placeholder="https://www.youtube.com/watch?v=..."
              />
              <button
                className="min-h-11 rounded bg-[var(--accent)] px-5 font-medium text-white hover:bg-[var(--accent-strong)]"
                type="button"
              >
                Generate
              </button>
            </div>
            <p className="mt-3 text-sm text-[var(--muted)]">
              API wiring comes next. This screen anchors the core paste-and-process flow.
            </p>
          </form>

          <aside className="rounded border border-[var(--border)] bg-[var(--panel)] p-5">
            <h2 className="text-base font-semibold">Foundation status</h2>
            <dl className="mt-4 grid gap-3 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-[var(--muted)]">Backend</dt>
                <dd>FastAPI scaffolded</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-[var(--muted)]">Frontend</dt>
                <dd>Next.js scaffolded</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-[var(--muted)]">Infra</dt>
                <dd>Postgres + Redis</dd>
              </div>
            </dl>
          </aside>
        </section>

        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {platforms.map((platform) => (
            <article
              className="rounded border border-[var(--border)] bg-[var(--panel)] p-4"
              key={platform}
            >
              <h2 className="font-medium">{platform}</h2>
              <p className="mt-2 text-sm text-[var(--muted)]">
                Platform generator slot reserved for the agent pipeline.
              </p>
            </article>
          ))}
        </section>
      </section>
    </main>
  );
}

