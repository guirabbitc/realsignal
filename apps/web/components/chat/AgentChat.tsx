"use client";

import { useEffect, useRef, useState } from "react";

import { Stone } from "@/components/ui/Stone";

import { formatReply } from "./format";

interface Message {
  from: "founder" | "agents";
  text: string;
}

// Shown before the first message, so opening the page does not call the agents.
const WELCOME: Message = {
  from: "agents",
  text: "Hi, I'm valiDate. Tell me the idea you are testing in one sentence, then paste the interview transcript. I'll hand it to my team of agents and come back with a verdict.",
};

function Reply({ text }: { text: string }) {
  return (
    <div className="flex flex-col gap-2.5">
      {formatReply(text).map((block, i) => {
        if (block.kind === "heading") return <p key={i} className="m-0 font-bold">{block.text}</p>;
        if (block.kind === "note") return <p key={i} className="m-0 text-sm text-muted">{block.text}</p>;
        if (block.kind === "paragraph") return <p key={i} className="m-0 leading-normal">{block.text}</p>;
        const List = block.kind === "steps" ? "ol" : "ul";
        return (
          <List key={i} className={`m-0 flex flex-col gap-1.5 pl-5 leading-normal ${block.kind === "steps" ? "list-decimal" : "list-disc"}`}>
            {block.items.map((item, j) => (
              <li key={j}>{item}</li>
            ))}
          </List>
        );
      })}
    </div>
  );
}

/** `compact` is the floating window (ChatWidget): no title, and the messages scroll inside a fixed height. */
export function AgentChat({ compact = false }: { compact?: boolean }) {
  const [messages, setMessages] = useState<Message[]>([WELCOME]);
  const [draft, setDraft] = useState("");
  const [waiting, setWaiting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => {
    end.current?.scrollIntoView({ block: "end" });
  }, [messages, waiting]);

  async function send() {
    const text = draft.trim();
    if (!text || waiting) return;
    setMessages((all) => [...all, { from: "founder", text }]);
    setDraft("");
    setError(null);
    setWaiting(true);
    try {
      const response = await fetch("/api/agent-chat", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const body = await response.json().catch(() => null);
      if (!response.ok) throw new Error(body?.error?.message ?? "The agents could not answer.");
      setMessages((all) => [...all, { from: "agents", text: body.reply }]);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "The agents could not answer.");
      setDraft(text);
    } finally {
      setWaiting(false);
    }
  }

  return (
    <section aria-label="Chat with the agents" className={compact ? "flex min-h-0 flex-1 flex-col" : "flex flex-col gap-6"}>
      {!compact && (
        <div className="flex flex-col gap-1.5">
          <h1 className="m-0 font-serif text-[clamp(34px,4.4vw,52px)] leading-[1.05] font-medium tracking-[-0.02em]">Chat with the agents</h1>
          <span className="text-base text-ink-soft">
            The same team of Fetch.ai agents you can talk to in ASI:One: Intake, Signal Analyst and Strategist.
          </span>
        </div>
      )}

      <div className={compact ? "flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-4 py-4" : "card flex flex-col gap-4 px-5 py-5"} aria-live="polite">
        {messages.map((message, i) =>
          message.from === "agents" ? (
            <div key={i} className="flex items-start gap-3">
              <span className="shrink-0 pt-0.5"><Stone kind="real" size={26} /></span>
              <div className="min-w-0 flex-1 text-[16px] text-ink"><Reply text={message.text} /></div>
            </div>
          ) : (
            <div key={i} className="ml-auto max-w-[85%] rounded-xl border-[2.5px] border-ink bg-real-tint px-4 py-2.5 text-[16px] whitespace-pre-wrap text-ink">
              {message.text.length > 600 ? `${message.text.slice(0, 600)}…` : message.text}
            </div>
          ),
        )}
        {waiting && (
          <p className="m-0 text-[15px] text-muted motion-safe:animate-pulse-soft">
            The agents are working on it. A full interview can take a minute.
          </p>
        )}
        {error && (
          <p role="alert" className="m-0 text-[15px] font-bold text-danger">
            {error} Your message is back in the box, so you can send it again.
          </p>
        )}
        <div ref={end} />
      </div>

      <form
        className={compact ? "flex flex-col gap-2 border-t-[2.5px] border-ink px-4 py-3" : "flex flex-col gap-3"}
        onSubmit={(event) => {
          event.preventDefault();
          void send();
        }}
      >
        <label htmlFor="agent-chat-message" className={compact ? "sr-only" : "text-[15px] font-bold text-ink"}>
          Your message
        </label>
        <textarea
          id="agent-chat-message"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          // In the small window Enter sends, as in a messenger; a pasted transcript keeps its line breaks.
          onKeyDown={(event) => {
            if (compact && event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault();
              void send();
            }
          }}
          rows={compact ? 2 : 5}
          placeholder={
            compact
              ? "Your idea, or paste the transcript"
              : "Your idea in one sentence, or the transcript:\nFounder: How do you handle bookings today?\nCustomer: I answer them myself between services."
          }
          className="w-full rounded-xl border-[2.5px] border-ink bg-white px-4 py-3 text-[16px] text-ink"
        />
        <button type="submit" disabled={waiting || !draft.trim()} className="btn btn-primary self-start px-6 disabled:cursor-not-allowed disabled:opacity-60">
          {waiting ? "Sending…" : "Send"}
        </button>
      </form>
    </section>
  );
}
