// The web chat with the Fetch.ai agents. One message in, the front agent's reply out.
import { z } from "zod";

import { AgentCallError, chatWithAgent } from "@/lib/agent-client";
import { invalid, json, readJson } from "@/lib/http";
import { getOrCreateFounderId } from "@/lib/session";

export const maxDuration = 300;

const MAX_MESSAGE_CHARS = 80_000;
const chatSchema = z.object({ text: z.string().trim().min(1).max(MAX_MESSAGE_CHARS) });

const MESSAGES: Record<AgentCallError["code"], string> = {
  agent_not_configured: "The agent chat is not set up on this server.",
  agent_unreachable: "The agents are offline right now.",
  timeout: "The agents took too long to answer.",
  bad_key: "The agent chat is not set up correctly on this server.",
  agent_error: "The agents could not answer.",
};

export async function POST(request: Request) {
  const parsed = chatSchema.safeParse(await readJson(request));
  if (!parsed.success) return invalid(`Send {text (max ${MAX_MESSAGE_CHARS} chars)}.`);
  // The founder id is the chat session, so the agent keeps one conversation per founder.
  const founderId = await getOrCreateFounderId();
  try {
    return json({ reply: await chatWithAgent(founderId, parsed.data.text) });
  } catch (error) {
    const code = error instanceof AgentCallError ? error.code : "agent_error";
    console.warn(`agent chat failed code=${code}`);
    return json({ error: { code, message: MESSAGES[code] } }, code === "timeout" ? 504 : 503);
  }
}
