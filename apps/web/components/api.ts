"use client";

// Typed calls to the web API from the browser. The session cookie rides along on same-origin
// requests; the UI never sees or sends a founder id (SPEC §7).
import { useCallback, useEffect, useState } from "react";

import type { Verdict } from "@/lib/contracts";

import type { InterviewStatus } from "./read-out/view-model";

/** GET /api/ideas */
export interface IdeaSummary {
  id: string;
  one_liner: string;
  target_customer: string | null;
  interview_count: number;
  latest_verdict: Verdict | null;
  created_at: string;
}

export interface IdeaInterviewRow {
  id: string;
  kind: "interview" | "demo";
  interviewee_label: string | null;
  status: InterviewStatus;
  score: number | null;
  verdict: Verdict | null;
  created_at: string;
}

/** GET /api/ideas/:id (interviews newest first) */
export interface IdeaDetail {
  id: string;
  one_liner: string;
  target_customer: string | null;
  interviews: IdeaInterviewRow[];
}

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string | null,
  ) {
    super(`API ${status}${code ? ` ${code}` : ""}`);
  }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { cache: "no-store", ...init });
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body?.error?.code ?? null);
  return body as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return call<T>(path);
}

export function apiPost<T>(path: string, payload: unknown): Promise<T> {
  return call<T>(path, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
}

export type Loaded<T> = { state: "loading" } | { state: "missing" } | { state: "error" } | { state: "ready"; data: T };

/**
 * Loads `path`; a 404 is "missing", anything else that fails is "error".
 * `refresh` reloads quietly (for polling); `retry` shows the loading state again first.
 */
export function useApi<T>(path: string): { load: Loaded<T>; refresh: () => void; retry: () => void } {
  const [attempt, setAttempt] = useState(0);
  const [load, setLoad] = useState<Loaded<T>>({ state: "loading" });
  useEffect(() => {
    let cancelled = false;
    apiGet<T>(path).then(
      (data) => !cancelled && setLoad({ state: "ready", data }),
      (error) => !cancelled && setLoad(error instanceof ApiError && error.status === 404 ? { state: "missing" } : { state: "error" }),
    );
    return () => {
      cancelled = true;
    };
  }, [path, attempt]);
  const refresh = useCallback(() => setAttempt((a) => a + 1), []);
  const retry = useCallback(() => {
    setLoad({ state: "loading" });
    setAttempt((a) => a + 1);
  }, []);
  return { load, refresh, retry };
}
