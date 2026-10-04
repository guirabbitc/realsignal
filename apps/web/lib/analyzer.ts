// The only place the web app talks to the analyzer.
import Ajv2020 from "ajv/dist/2020";
import schema from "@realsignal/contracts/analyze.schema.json";
import type { AnalyzeRequest, AnalyzeResponse } from "./contracts/analyze";

const ajv = new Ajv2020({ strict: false });
const validateResponse = ajv.compile<AnalyzeResponse>({
  ...schema.$defs.AnalyzeResponse,
  $defs: schema.$defs,
});

function config() {
  const url = process.env.ANALYZER_URL;
  const secret = process.env.ANALYZER_SECRET;
  if (!url || !secret) throw new Error("ANALYZER_URL and ANALYZER_SECRET must be set");
  return { endpoint: `${url.replace(/\/$/, "")}/analyze`, secret };
}

async function send(body: BodyInit, headers: Record<string, string>): Promise<AnalyzeResponse> {
  const { endpoint, secret } = config();
  const response = await fetch(endpoint, {
    method: "POST",
    headers: { ...headers, "X-Analyzer-Key": secret },
    body,
  });
  if (!response.ok) {
    throw new Error(`Analyzer returned ${response.status}: ${(await response.text()).slice(0, 500)}`);
  }
  const data: unknown = await response.json();
  if (!validateResponse(data)) {
    throw new Error(`Analyzer response does not match the contract: ${ajv.errorsText(validateResponse.errors)}`);
  }
  return data;
}

export function analyzeTranscript(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  return send(JSON.stringify(request), { "Content-Type": "application/json" });
}

// Audio goes straight to the analyzer and is not persisted (open question: audio storage).
export function analyzeAudio(idea: string, file: File): Promise<AnalyzeResponse> {
  const form = new FormData();
  form.set("idea", idea);
  form.set("file", file, file.name);
  return send(form, {});
}
