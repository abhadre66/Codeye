import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");

  if (code) {
    const cookieStore = await cookies();
    const supabase = createServerClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL!,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
      {
        cookies: {
          getAll: () => cookieStore.getAll(),
          setAll: (cookiesToSet) =>
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            ),
        },
      }
    );

    const { data, error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) {
      console.error("exchangeCodeForSession failed:", error.message);
    }

    // Save GitHub token to profiles table right after OAuth.
    // Call the backend directly (not through this same deployment's /api
    // rewrite) to avoid a self-referential hairpin request.
    if (data.session?.provider_token && data.session?.access_token) {
      const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
      try {
        const res = await fetch(`${backendUrl}/profile/github-token`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${data.session.access_token}`,
          },
          body: JSON.stringify({ github_token: data.session.provider_token }),
        });
        if (!res.ok) {
          console.error("Failed to save GitHub token:", res.status, await res.text().catch(() => ""));
        }
      } catch (err) {
        console.error("Failed to save GitHub token:", err);
      }
    } else {
      console.warn("No provider_token after OAuth exchange — GitHub token was not saved.");
    }
  }

  return NextResponse.redirect(origin);
}
