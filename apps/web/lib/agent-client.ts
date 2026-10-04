// The ONLY code that calls the Fetch.ai front agent (agents/front/agent.py, POST /chat).
// The agent runs the same conversation it has in ASI:One, so a web chat goes through the same
// specialist agents. It is reached on its own port, so it needs AGENT_URL to be reachable from here.

const CHAT_TIMEOUT_MS = 240_000;

export class AgentCallError extends Error {
  constructor(public readonly code: "agent_not_configured" | "agent_unreachable" | "timeout" | "bad_key" | "agent_error") {
    super(`agent call failed: ${code}`);
  }
}

/** `session` identifies the founder to the agent, so it remembers their idea between messages. */
export async function chatWithAgent(session: string, text: string): Promise<string> {
  const url = process.env.AGENT_URL;
  const key = process.env.AGENT_CHAT_KEY;
  if (!url || !key) throw new AgentCallError("agent_not_configured");

  let response: Response;
  try {
    response = await fetch(`${url.replace(/\/$/, "")}/chat`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ key, session, text }),
      signal: AbortSignal.timeout(CHAT_TIMEOUT_MS),
    });
  } catch (error) {
    throw new AgentCallError(error instanceof Error && error.name === "TimeoutError" ? "timeout" : "agent_unreachable");
  }
  const body = (await response.json().catch(() => null)) as { ok?: boolean; reply?: string } | null;
  if (!response.ok || !body || typeof body.reply !== "string") throw new AgentCallError("agent_error");
  if (!body.ok) throw new AgentCallError(body.reply === "bad_key" ? "bad_key" : "agent_error");
  return body.reply;
}
