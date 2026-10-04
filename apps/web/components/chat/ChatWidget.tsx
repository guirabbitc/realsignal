"use client";

import { useEffect, useState } from "react";

import { Stone } from "@/components/ui/Stone";

import { AgentChat } from "./AgentChat";

// The front agent's public page, where the same agent can be opened in ASI:One. Optional.
const PROFILE_URL = process.env.NEXT_PUBLIC_AGENT_PROFILE_URL;

/** The agent chat as a small window over any page. */
export function ChatWidget() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      {/* Hidden, not unmounted, so closing the window keeps the conversation and a reply in flight. */}
      <div
        id="chat-widget"
        role="dialog"
        aria-label="Chat with the agents"
        hidden={!open}
        className="fixed right-3 bottom-[84px] z-20 flex h-[min(600px,calc(100vh-108px))] w-[min(400px,calc(100vw-24px))] flex-col overflow-hidden rounded-2xl border-[2.5px] border-ink bg-paper shadow-[4px_4px_0_var(--color-ink)] wide:right-6 [&[hidden]]:hidden"
      >
        <div className="flex items-center justify-between gap-3 border-b-[2.5px] border-ink bg-white px-4 py-2.5">
          <div className="flex min-w-0 flex-col">
            <span className="text-[15px] font-bold text-ink">valiDate agents</span>
            <span className="text-[13px] text-muted">
              Fetch.ai team, as in ASI:One
              {PROFILE_URL && (
                <>
                  {" · "}
                  <a href={PROFILE_URL} target="_blank" rel="noreferrer" className="font-bold text-ink">
                    Agent profile
                  </a>
                </>
              )}
            </span>
          </div>
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close the chat"
            className="min-h-9 shrink-0 cursor-pointer rounded-lg border-[2.5px] border-ink bg-white px-2.5 text-[15px] font-bold text-ink hover:bg-line"
          >
            Close
          </button>
        </div>
        <AgentChat compact />
      </div>

      <button
        type="button"
        onClick={() => setOpen((was) => !was)}
        aria-expanded={open}
        aria-controls="chat-widget"
        aria-label={open ? "Close the chat" : "Chat with the agents"}
        className="fixed right-3 bottom-4 z-20 flex min-h-14 cursor-pointer items-center gap-2 rounded-full border-[2.5px] border-ink bg-white py-2 pr-5 pl-3.5 text-[15px] font-bold text-ink shadow-[3px_3px_0_var(--color-ink)] hover:bg-real-tint wide:right-6"
      >
        <Stone kind="real" size={28} />
        {open ? "Close" : "Ask the agents"}
      </button>
    </>
  );
}
