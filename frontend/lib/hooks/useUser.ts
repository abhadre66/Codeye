"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import type { User } from "@supabase/supabase-js";

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
        fetch("/api/profile/github-token", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
          body: JSON.stringify({ github_token: providerToken }),
        }).catch(() => {});
      }
    };

    init();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null);

      // After GitHub OAuth sign-in, save the provider_token (GitHub token) to backend
      if (event === "SIGNED_IN" && session?.provider_token) {
        fetch("/api/profile/github-token", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${session.access_token}`,
          },
          body: JSON.stringify({ github_token: session.provider_token }),
        }).catch(() => {});
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
