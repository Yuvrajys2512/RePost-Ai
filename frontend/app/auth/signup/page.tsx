"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { supabase } from "@/lib/supabase";

export default function Signup() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  async function handleSignup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!email || !password || !confirmPassword) {
      setError("Please fill in all fields.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const { data, error: authError } = await supabase.auth.signUp({
        email,
        password,
      });

      if (authError) {
        throw new Error(authError.message);
      }

      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed.");
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
          <h1 className="mt-2 text-2xl font-bold tracking-tight">Create your account</h1>
          <p className="mt-2 text-sm text-[var(--muted)]">
            Start repurposing your video content like a pro
          </p>
        </header>

        <form className="mt-8 space-y-5" onSubmit={handleSignup}>
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
            <label className="text-sm font-medium leading-none" htmlFor="password">
              Password
            </label>
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

          <div className="space-y-2">
            <label className="text-sm font-medium leading-none" htmlFor="confirm-password">
              Confirm Password
            </label>
            <input
              id="confirm-password"
              type="password"
              className="flex h-11 w-full border border-[var(--border)] bg-white px-3 py-2 text-sm outline-none transition-colors focus:border-[var(--accent)]"
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              disabled={isLoading}
            />
          </div>

          <button
            type="submit"
            className="flex h-11 w-full items-center justify-center bg-[var(--accent)] px-4 py-2 font-medium text-white transition-all hover:bg-[var(--accent-strong)] disabled:cursor-not-allowed disabled:bg-[var(--disabled)]"
            disabled={isLoading}
          >
            {isLoading ? "Creating account..." : "Sign up with Email"}
          </button>
        </form>

        <footer className="mt-6 text-center text-sm text-[var(--muted)]">
          Already have an account?{" "}
          <Link
            href="/auth/login"
            className="font-medium text-[var(--accent)] hover:text-[var(--accent-strong)] hover:underline"
          >
            Log in
          </Link>
        </footer>
      </div>
    </main>
  );
}
