"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/lib/supabase";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email || !password) {
      setError("Please fill in all fields.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const { data, error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (authError) {
        throw new Error(authError.message);
      }

      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid email or password.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#f4f6f8] via-[#e2e8f0] to-[#cbd5e1] p-4 text-[var(--foreground)]">
      <div className="w-full max-w-md border border-[var(--border)] bg-[var(--panel)] p-8 shadow-xl backdrop-blur-md transition-all duration-300 hover:shadow-2xl">
        <header className="text-center">
          <p className="text-sm font-semibold uppercase tracking-wider text-[var(--accent)]">
            RePost AI
          </p>
          <h1 className="mt-2 text-2xl font-bold tracking-tight">Welcome back</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Sign in to access your content workspace
          </p>
        </header>

        <form className="mt-8 space-y-5" onSubmit={handleLogin}>
          {error && (
            <div className="border border-[var(--danger)] bg-[var(--danger-soft)] px-4 py-3 text-sm text-[var(--danger)]">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-medium leading-none" htmlFor="email">
              Email address
            </label>
            <input
              id="email"
              type="email"
              className="flex h-11 w-full border border-[var(--border)] bg-white px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--accent)]"
              placeholder="name@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium leading-none" htmlFor="password">
                Password
              </label>
            </div>
            <input
              id="password"
              type="password"
              className="flex h-11 w-full border border-[var(--border)] bg-white px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--accent)]"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            className="flex h-11 w-full items-center justify-center bg-[var(--accent)] px-4 py-2 font-medium text-white transition-all hover:bg-[var(--accent-strong)] disabled:cursor-not-allowed disabled:bg-[var(--disabled)]"
            disabled={isLoading}
          >
            {isLoading ? "Signing in..." : "Sign in with Email"}
          </button>
        </form>

        <footer className="mt-6 text-center text-sm text-[var(--muted)]">
          Don't have an account?{" "}
          <Link
            href="/auth/signup"
            className="font-medium text-[var(--accent)] hover:text-[var(--accent-strong)] hover:underline"
          >
            Sign up
          </Link>
        </footer>
      </div>
    </main>
  );
}
