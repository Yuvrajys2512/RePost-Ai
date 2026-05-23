import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

class MockSupabaseClient {
  auth = {
    async signUp({ email }: { email: string; password?: string }) {
      const mockUser = {
        id: "00000000-0000-0000-0000-000000000000",
        email,
      };
      const mockSession = {
        user: mockUser,
        access_token: "mock-user-token",
        expires_at: Math.floor(Date.now() / 1000) + 3600,
      };
      
      localStorage.setItem("repost_mock_session", JSON.stringify(mockSession));
      window.dispatchEvent(new Event("repost-auth-change"));
      
      return { data: { user: mockUser, session: mockSession }, error: null };
    },

    async signInWithPassword({ email }: { email: string; password?: string }) {
      const mockUser = {
        id: "00000000-0000-0000-0000-000000000000",
        email,
      };
      const mockSession = {
        user: mockUser,
        access_token: "mock-user-token",
        expires_at: Math.floor(Date.now() / 1000) + 3600,
      };
      
      localStorage.setItem("repost_mock_session", JSON.stringify(mockSession));
      window.dispatchEvent(new Event("repost-auth-change"));
      
      return { data: { user: mockUser, session: mockSession }, error: null };
    },

    async signOut() {
      localStorage.removeItem("repost_mock_session");
      window.dispatchEvent(new Event("repost-auth-change"));
      return { error: null };
    },

    async getSession() {
      if (typeof window === "undefined") {
        return { data: { session: null } };
      }
      const raw = localStorage.getItem("repost_mock_session");
      return { data: { session: raw ? JSON.parse(raw) : null } };
    },

    onAuthStateChange(
      callback: (event: string, session: any) => void
    ) {
      const handler = () => {
        const raw = localStorage.getItem("repost_mock_session");
        callback("SIGNED_IN", raw ? JSON.parse(raw) : null);
      };
      
      if (typeof window !== "undefined") {
        window.addEventListener("repost-auth-change", handler);
        // Execute immediately to sync initial load state
        handler();
      }

      return {
        data: {
          subscription: {
            unsubscribe: () => {
              if (typeof window !== "undefined") {
                window.removeEventListener("repost-auth-change", handler);
              }
            },
          },
        },
      };
    },
  };
}

// Instantiate either real Supabase or our Mock client based on configuration
export const supabase = (supabaseUrl && supabaseAnonKey)
  ? createClient(supabaseUrl, supabaseAnonKey)
  : (new MockSupabaseClient() as any);
