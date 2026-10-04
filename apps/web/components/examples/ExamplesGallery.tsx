"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { EXAMPLE_IDEAS, EXAMPLE_TYPES, EXAMPLES, type Example, type ExampleIdeaKey, type ExampleType } from "@/lib/examples";

import { runExample } from "./run";

export const TYPE_LABEL = Object.fromEntries(EXAMPLE_TYPES.map((t) => [t.type, t.label])) as Record<ExampleType, string>;

const IDEA_KEYS = Object.keys(EXAMPLE_IDEAS) as ExampleIdeaKey[];

/** Starts an example and opens its read-out; `running` is the key of the example being started. */
export function useRunExample() {
  const router = useRouter();
  const [running, setRunning] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const run = async (example: Example) => {
    setRunning(example.key);
    setError(null);
    try {
      router.push(`/interviews/${await runExample(example)}`);
    } catch {
      setRunning(null);
      setError("We couldn’t start that example. Check your connection and try again.");
    }
  };
  return { running, error, run };
}

function ExampleCard({ example, running, disabled, onRun }: { example: Example; running: boolean; disabled: boolean; onRun: () => void }) {
  return (
    <article className="card flex flex-col gap-3 p-5">
      <span className={`tag self-start ${example.type === "real_pain" ? "bg-real-tint" : ""}`}>{TYPE_LABEL[example.type]}</span>
      <strong className="text-base leading-snug">{example.intervieweeLabel}</strong>
      <p className="m-0 text-[15px] leading-normal text-ink-soft">{example.hook}</p>
      <button
        type="button"
        disabled={disabled}
        onClick={onRun}
        className="btn btn-primary mt-auto disabled:cursor-not-allowed disabled:border-stone-grey disabled:bg-line disabled:text-muted"
      >
        {running ? "Starting…" : "Run this example"}
      </button>
    </article>
  );
}

export function ExamplesGallery() {
  const [filter, setFilter] = useState<ExampleType | "all">("all");
  const { running, error, run } = useRunExample();
  const shown = EXAMPLES.filter((e) => filter === "all" || e.type === filter);
  const description = EXAMPLE_TYPES.find((t) => t.type === filter)?.description;
  const chips: { value: ExampleType | "all"; label: string }[] = [
    { value: "all", label: `All (${EXAMPLES.length})` },
    ...EXAMPLE_TYPES.map((t) => ({ value: t.type, label: t.label })),
  ];

  return (
    <section aria-label="Examples" className="flex flex-col gap-7">
      <div className="flex flex-col gap-2">
        <h1 className="m-0 font-serif text-[clamp(34px,4.4vw,52px)] leading-[1.05] font-medium tracking-[-0.02em]">Examples</h1>
        <p className="m-0 max-w-[640px] text-[17px] leading-normal text-pretty text-ink-soft">
          Made-up interviews between early-stage founders and the founders and tech leads they sell to. Pick one: we run it under its
          own example idea and open the read-out, usually in under a minute.
        </p>
      </div>

      <div className="flex flex-col gap-3">
        <div role="group" aria-label="Filter by type" className="flex flex-wrap gap-2">
          {chips.map((chip) => (
            <button
              key={chip.value}
              type="button"
              aria-pressed={filter === chip.value}
              onClick={() => setFilter(chip.value)}
              className={`min-h-10 cursor-pointer rounded-full border-[2.5px] border-ink px-4 font-sans text-sm font-bold ${
                filter === chip.value ? "bg-ink text-paper" : "bg-white text-ink hover:bg-line"
              }`}
            >
              {chip.label}
            </button>
          ))}
        </div>
        {description && <p className="m-0 text-[15px] text-muted">{description}</p>}
      </div>

      {error && (
        <p role="alert" className="m-0 text-[15px] font-bold text-danger">
          {error}
        </p>
      )}

      {IDEA_KEYS.map((ideaKey) => {
        const list = shown.filter((e) => e.idea === ideaKey);
        if (list.length === 0) return null;
        return (
          <div key={ideaKey} className="flex flex-col gap-3.5">
            <h2 className="m-0 font-serif text-2xl leading-tight font-medium text-pretty">{EXAMPLE_IDEAS[ideaKey]}</h2>
            <div className="grid grid-cols-[repeat(auto-fill,minmax(min(100%,280px),1fr))] gap-4">
              {list.map((example) => (
                <ExampleCard
                  key={example.key}
                  example={example}
                  running={running === example.key}
                  disabled={running !== null}
                  onRun={() => run(example)}
                />
              ))}
            </div>
          </div>
        );
      })}
    </section>
  );
}
