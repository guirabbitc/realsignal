// Runs one analysis for an interview that is already saved, and stores the result or the error code.
// Called inside after(), both for a new interview and for "Try again" on a failed one.
import { AnalyzerCallError, analyze } from "./analyzer-client";
import type { AnalyzeRequest } from "./contracts";
import { markInterviewFailed, saveAnalysis } from "./db/queries";

export async function runAnalysis(founderId: string, interviewId: string, request: AnalyzeRequest): Promise<void> {
  const started = Date.now();
  try {
    const result = await analyze(request);
    await saveAnalysis(founderId, interviewId, result);
    console.info(`analysis done interview=${interviewId} ms=${Date.now() - started} verdict=${result.verdict}`);
  } catch (error) {
    const code = error instanceof AnalyzerCallError ? error.code : "internal_error";
    await markInterviewFailed(founderId, interviewId, code);
    console.warn(`analysis failed interview=${interviewId} ms=${Date.now() - started} code=${code}`);
  }
}
