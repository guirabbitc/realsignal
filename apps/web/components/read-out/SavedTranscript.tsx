"use client";

// Shown when an analysis failed: the transcript is safe on our side, and the founder can keep their own copy.
import { useState } from "react";

export function SavedTranscript({ text }: { text: string }) {
  const [copy, setCopy] = useState<"idle" | "copied" | "failed">("idle");

  async function copyText() {
    try {
      await navigator.clipboard.writeText(text);
      setCopy("copied");
    } catch {
      setCopy("failed");
    }
  }

  function download() {
    const url = URL.createObjectURL(new Blob([text], { type: "text/plain;charset=utf-8" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = "interview-transcript.txt";
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <section aria-label="Your saved transcript" className="card flex flex-col gap-3.5 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-col gap-1">
          <h2 className="m-0 text-[17px] font-bold">Your transcript is saved</h2>
          <span className="text-sm text-muted">Nothing was lost. Try again above, or keep your own copy.</span>
        </div>
        <div className="flex flex-wrap gap-2.5">
          <button type="button" className="btn btn-secondary" onClick={copyText}>
            {copy === "copied" ? "Copied" : "Copy transcript"}
          </button>
          <button type="button" className="btn btn-secondary" onClick={download}>
            Download .txt
          </button>
        </div>
      </div>
      {copy === "failed" && (
        <span role="status" className="text-sm text-ink-soft">
          Your browser blocked copying. Select the text below and copy it, or download it.
        </span>
      )}
      <pre className="m-0 max-h-[360px] overflow-auto rounded-[14px] border-[2.5px] border-ink bg-paper p-4 font-mono text-[14px] leading-relaxed whitespace-pre-wrap text-ink">
        {text}
      </pre>
    </section>
  );
}
