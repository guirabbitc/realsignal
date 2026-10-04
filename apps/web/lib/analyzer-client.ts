// The ONLY code that calls the analyzer (SPEC §4 rule 2). Every call sends X-Analyzer-Key.
import type { AnalyzeRequest, AnalyzeResult } from "./contracts";

const ANALYZE_TIMEOUT_MS = 120_000;
const HEALTH_TIMEOUT_MS = 2_000;

export class AnalyzerCallError extends Error {
  constructor(public readonly code: string) {
    super(`analyzer call failed: ${code}`);
  }
}

function baseUrl(): string {
  const url = process.env.ANALYZER_URL;
  if (!url) throw new AnalyzerCallError("analyzer_not_configured");
  return url.replace(/\/$/, "");
}

export async function analyze(request: AnalyzeRequest): Promise<AnalyzeResult> {
  let response: Response;
  try {
    response = await fetch(`${baseUrl()}/analyze`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-analyzer-key": process.env.ANALYZER_KEY ?? "" },
      body: JSON.stringify(request),
      signal: AbortSignal.timeout(ANALYZE_TIMEOUT_MS),
    });
  } catch (error) {
    throw new AnalyzerCallError(error instanceof Error && error.name === "TimeoutError" ? "timeout" : "analyzer_unreachable");
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new AnalyzerCallError(body?.error?.code ?? `http_${response.status}`);
  return body as AnalyzeResult;
}

export async function analyzerHealthy(): Promise<boolean> {
  try {
    const response = await fetch(`${baseUrl()}/health`, { signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS) });
    return response.ok && (await response.json())?.status === "ok";
  } catch {
    return false;
  }
}
