import { afterEach, describe, expect, it, vi } from "vitest";

import { formatReply } from "../components/chat/format";
import { AgentCallError, chatWithAgent } from "../lib/agent-client";

describe("formatReply", () => {
  it("turns an agent read-out into headings, notes, paragraphs and lists", () => {
    const reply = [
      "_I read Interviewer as you and Priya as the customer._",
      "",
      "**Verdict: Keep going**",
      "",
      "Signal score: 97 / 100",
      "**Why**",
      "- They pay for a workaround today [#9].",
      "- They asked to start `this week`.",
      "**Ask next**",
      "1. What did it cost?",
      "2. Who else decides?",
    ].join("\n");
    expect(formatReply(reply)).toEqual([
      { kind: "note", text: "I read Interviewer as you and Priya as the customer." },
      { kind: "heading", text: "Verdict: Keep going" },
      { kind: "paragraph", text: "Signal score: 97 / 100" },
      { kind: "heading", text: "Why" },
      { kind: "bullets", items: ["They pay for a workaround today [#9].", "They asked to start this week."] },
      { kind: "heading", text: "Ask next" },
      { kind: "steps", items: ["What did it cost?", "Who else decides?"] },
    ]);
  });
});

describe("chatWithAgent", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.unstubAllGlobals();
  });

  it("fails clearly when the agent is not configured", async () => {
    vi.stubEnv("AGENT_URL", "");
    vi.stubEnv("AGENT_CHAT_KEY", "");
    await expect(chatWithAgent("s", "hi")).rejects.toMatchObject({ code: "agent_not_configured" });
  });

  it("sends the key and the session, and returns the reply", async () => {
    vi.stubEnv("AGENT_URL", "http://agent.test/");
    vi.stubEnv("AGENT_CHAT_KEY", "k");
    const fetchMock = vi.fn(async () => Response.json({ ok: true, reply: "Hello" }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(chatWithAgent("founder-1", "hi")).resolves.toBe("Hello");
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe("http://agent.test/chat");
    expect(JSON.parse(init.body as string)).toEqual({ key: "k", session: "founder-1", text: "hi" });
  });

  it("maps an offline agent and a rejected key to their own codes", async () => {
    vi.stubEnv("AGENT_URL", "http://agent.test");
    vi.stubEnv("AGENT_CHAT_KEY", "k");
    vi.stubGlobal("fetch", vi.fn(async () => { throw new TypeError("fetch failed"); }));
    await expect(chatWithAgent("s", "hi")).rejects.toMatchObject({ code: "agent_unreachable" });
    vi.stubGlobal("fetch", vi.fn(async () => Response.json({ ok: false, reply: "bad_key" })));
    await expect(chatWithAgent("s", "hi")).rejects.toBeInstanceOf(AgentCallError);
    await expect(chatWithAgent("s", "hi")).rejects.toMatchObject({ code: "bad_key" });
  });
});
