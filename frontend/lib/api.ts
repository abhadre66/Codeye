import { supabase } from "@/lib/supabase";

const BASE = "/api";

async function getToken(): Promise<string | null> {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

export class ApiError extends Error {
  status: number;
  code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, options);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new ApiError(err.detail || `HTTP ${res.status}`, res.status, err.code);
  }
  return res.json();
}

async function post<T>(path: string, body: unknown, withAuth = false): Promise<T> {
  const token = withAuth ? await getToken() : null;
  return req<T>(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });
}

function get<T>(path: string): Promise<T> {
  return req<T>(path);
}

// ── Analysis ──────────────────────────────────────────────────────────────────
export const analyzePaste = (code: string, filename = "snippet.py") =>
  post<{ ok: boolean; result: unknown }>("/analyze/paste", { code, filename });

export const analyzeUpload = (files: { name: string; content: string }[]) =>
  post<{ ok: boolean; results: unknown[] }>("/analyze/upload", { files });

export const compare = (before: string, after: string, filename = "snippet.py") =>
  post<{ ok: boolean; result: unknown }>("/compare", { before, after, filename });

export const suggestFixes = (code: string, filename = "snippet.py", source: "paste" | "upload" = "paste") =>
  post<{ ok: boolean; result: unknown }>("/fix", { code, filename, source }, true);

// ── GitHub browse ─────────────────────────────────────────────────────────────
export interface RepoSummary {
  owner: string;
  name: string;
  full_name: string;
  private: boolean;
  description: string;
  default_branch: string;
  pushed_at: string;
  open_issues: number;
}

export interface PRListItem {
  number: number;
  title: string;
  author: string;
  head_branch: string;
  base_branch: string;
  updated_at: string;
  draft: boolean;
  url: string;
}

export const listRepos = async (page = 1) => {
  const token = await getToken();
  return req<{ ok: boolean; repos: RepoSummary[] }>(`/github/repos?page=${page}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
};

export const listOpenPRs = async (owner: string, repo: string) => {
  const token = await getToken();
  return req<{ ok: boolean; pulls: PRListItem[] }>(
    `/github/repos/${owner}/${repo}/pulls`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} },
  );
};

// ── PR ────────────────────────────────────────────────────────────────────────
export const analyzePR = (owner: string, repo: string, pr_number: number) =>
  post<{ ok: boolean; result: unknown }>("/pr/analyze", { owner, repo, pr_number }, true);

export interface PRFileContent {
  filename: string;
  before: string;
  after: string;
  status: string;
  additions: number;
  deletions: number;
}

export const getPRFilesContent = async (owner: string, repo: string, pr_number: number) => {
  const token = await getToken();
  return req<{ ok: boolean; files: PRFileContent[] }>(
    `/pr/files/content?owner=${owner}&repo=${repo}&pr_number=${pr_number}`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} },
  );
};

export const getPRDiff = async (owner: string, repo: string, pr_number: number) => {
  const token = await getToken();
  return req<{ ok: boolean; raw_diff: string; files: unknown[] }>(
    `/pr/diff?owner=${owner}&repo=${repo}&pr_number=${pr_number}`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} },
  );
};

export const getPRContext = async (owner: string, repo: string, pr_number: number) => {
  const token = await getToken();
  return req<{ ok: boolean; result: unknown }>(
    `/pr/context?owner=${owner}&repo=${repo}&pr_number=${pr_number}`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} },
  );
};

export const getReviewers = async (owner: string, repo: string, pr_number: number) => {
  const token = await getToken();
  return req<{ ok: boolean; result: unknown[] }>(
    `/pr/reviewers?owner=${owner}&repo=${repo}&pr_number=${pr_number}`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} },
  );
};

export const postReview = (
  owner: string, repo: string, pr_number: number,
  body: string, event: string, confirmed: boolean,
  comments: unknown[] = [],
) =>
  post<{ ok: boolean; result: unknown }>("/pr/review", { owner, repo, pr_number, body, event, confirmed, comments }, true);

// ── History ───────────────────────────────────────────────────────────────────
export type HistoryStatus = "pending" | "fixed" | "dismissed";

export interface HistoryEntry {
  id: number;
  source: "paste" | "upload" | "pr";
  label: string;
  findings_count: number;
  security_count: number;
  style_count: number;
  status: HistoryStatus;
  created_at: string;
}

export const getHistory = async () => {
  const token = await getToken();
  return req<{ ok: boolean; history: HistoryEntry[] }>("/history", {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
};

export const getHistoryEntry = async (id: number) => {
  const token = await getToken();
  return req<{ ok: boolean; id: number; source: string; label: string; status: HistoryStatus; created_at: string; payload: Record<string, unknown> }>(
    `/history/${id}`,
    { headers: token ? { Authorization: `Bearer ${token}` } : {} },
  );
};

export const updateHistoryStatus = async (id: number, status: HistoryStatus) => {
  const token = await getToken();
  return req<{ ok: boolean; id: number; status: HistoryStatus }>(`/history/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ status }),
  });
};
