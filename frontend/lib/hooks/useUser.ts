"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import type { User } from "@supabase/supabase-js";

async function saveGithubToken(accessToken: string, githubToken: string) {
  try {
    const res = await fetch("/api/profile/github-token", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ github_token: githubToken }),
    });
    if (!res.ok) {
      const body = await res.text().catch(() => "");
      console.error("Failed to save GitHub token:", res.status, body);
    }
  } catch (err) {
    console.error("Failed to save GitHub token:", err);
  }
}

export function useUser() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      const { data, error } = await supabase.auth.getUser();
      if (error || !data.user) {
        await supabase.auth.signOut({ scope: "local" });
        setUser(null);
        setLoading(false);
        return;
      }

      setUser(data.user);
      setLoading(false);

      // Save GitHub token from session if profile doesn't have it yet
      const { data: sessionData } = await supabase.auth.getSession();
      const providerToken = sessionData.session?.provider_token;
      const accessToken = sessionData.session?.access_token;
      if (providerToken && accessToken) {
        saveGithubToken(accessToken, providerToken);
      } else {
        console.warn("No provider_token in session — GitHub token was not (re)saved.");
      }
    };

    init();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null);

      // After GitHub OAuth sign-in, save the provider_token (GitHub token) to backend
      if (event === "SIGNED_IN") {
        if (session?.provider_token && session.access_token) {
          saveGithubToken(session.access_token, session.provider_token);
        } else {
          console.warn("SIGNED_IN without provider_token — GitHub token was not saved.");
        }
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const signInWithGitHub = () =>
    supabase.auth.signInWithOAuth({
      provider: "github",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });

  const signOut = () => supabase.auth.signOut();

  return { user, loading, signInWithGitHub, signOut };
}
