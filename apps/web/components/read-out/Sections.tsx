"use client";

import { Fragment, useEffect, useRef, useState } from "react";

import { Stone } from "@/components/ui/Stone";
import type { AnalyzeResult, Statement } from "@/lib/contracts";

import {
  CATEGORY_LABEL,
  countGroups,
  founderFlags,
  groupOf,
  percent,
  splitRefs,
  topPolite,
  topReal,
  VERDICT_LABEL,
  VERDICT_STONE,
  type FounderFlag,
} from "./view-model";

const h2 = "m-0 font-serif text-[26px] font-medium";

function prefersReducedMotion() {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** Writer text with `[#12]` turned into links to that transcript line. The words are not changed. */
export function RefText({ text, positions }: { text: string; positions: Set<number> }) {
  return (
    <>
      {splitRefs(text, positions).map((part, i) =>
        "ref" in part ? (
          <a key={i} href={`#line-${part.ref}`} className="font-mono font-bold">
            {part.text}
          </a>
        ) : (
          <Fragment key={i}>{part.text}</Fragment>
        ),
      )}
    </>
  );
}

// Counts up to the API's score once, when the founder watched the analysis finish. Display only.
function useCountUp(target: number | null, animate: boolean) {
  const [shown, setShown] = useState(() => (animate && target !== null && !prefersReducedMotion() ? 0 : target));
  useEffect(() => {
    if (target === null || shown === target) return;
    const start = performance.now();
    let frame = requestAnimationFrame(function step(now) {
      const p = Math.min(1, (now - start) / 900);
      setShown(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) frame = requestAnimationFrame(step);
    });
    return () => cancelAnimationFrame(frame);
    // Runs once per target; `shown` only gates the first run.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [target]);
  return shown;
}

export function VerdictCard({ result, animate, positions }: { result: AnalyzeResult; animate: boolean; positions: Set<number> }) {
  const shown = useCountUp(result.score, animate);
  const counts = countGroups(result.statements);
  return (
    <section aria-label="Verdict" className="card flex flex-col gap-[22px] px-6 py-7 wide:px-8">
      <div className="flex flex-wrap justify-between gap-3">
        <span className="text-[13px] font-bold text-muted">Verdict</span>
        <span className="text-sm text-muted">
          {result.verdict_confidence === null ? "Confidence not measured" : `${percent(result.verdict_confidence)} confidence`}
        </span>
      </div>
      <div className="flex flex-wrap items-center gap-5">
        <Stone kind={VERDICT_STONE[result.verdict]} size={52} />
        <div className="flex min-w-0 flex-[1_1_300px] flex-col gap-2.5">
          <p className="m-0 font-serif text-[clamp(30px,4vw,44px)] leading-[1.05] font-medium tracking-[-0.02em]">
            {VERDICT_LABEL[result.verdict]}
          </p>
          {result.summary && (
            <p className="m-0 text-[17px] leading-normal text-ink-soft">
              <RefText text={result.summary} positions={positions} />
            </p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1">
          <span aria-hidden="true" className="min-w-[2ch] text-right font-mono text-[56px] leading-none font-bold tabular-nums">
            {shown ?? "—"}
          </span>
          <span className="sr-only">{result.score === null ? "No signal score." : `Signal score ${result.score} out of 100.`}</span>
          <span aria-hidden="true" className="text-[13px] font-bold text-muted">
            Signal score out of 100
          </span>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-3 border-t-[2.5px] border-ink pt-[18px] text-[15px]">
        <span className="flex items-center gap-2">
          <span aria-hidden="true" className="flex h-4 gap-[3px]">
            <span className="w-1 rounded-sm bg-ink" />
            <span className="w-5 rounded-[5px_5px_5px_2px] bg-real-tint" />
          </span>
          <strong>{counts.real}</strong> real
        </span>
        <span className="flex items-center gap-2">
          <span aria-hidden="true" className="h-4 w-6 rounded-[5px_5px_5px_2px] border-2 border-dashed border-stone-grey" />
          <strong>{counts.polite}</strong> polite
        </span>
        <span>
          <strong>{counts.neutral}</strong> small talk
        </span>
        {result.founder_talk_ratio !== null && (
          <span className="text-ink-soft wide:ml-auto">You talked {percent(result.founder_talk_ratio)} of the time.</span>
        )}
      </div>
    </section>
  );
}

export function MissingEvidence({ text }: { text: string | null }) {
  return (
    <div className="flex items-start gap-4 rounded-[22px] border-[2.5px] border-dashed border-ink bg-white px-6 py-[22px]">
      <Stone kind="unsure" size={36} />
      <div className="flex flex-col gap-1.5">
        <strong className="text-[17px]">What’s missing</strong>
        {text && <span className="text-[15px] leading-relaxed text-ink-soft">{text}</span>}
        <span className="text-[15px] leading-relaxed text-ink-soft">
          This is not a no. Ask the questions below in your next interview, then add it here.
        </span>
      </div>
    </div>
  );
}

function StatementLabel({ s }: { s: Statement }) {
  const real = groupOf(s.category) === "real";
  return (
    <div className="flex flex-wrap items-baseline gap-2.5">
      <span className={`text-sm font-bold ${real ? "text-brand" : "text-muted"}`}>{CATEGORY_LABEL[s.category]}</span>
      <span className="font-mono text-xs text-muted">real signal {percent(s.p_real)}</span>
    </div>
  );
}

/** A customer sentence. `quote` is rendered exactly as the API returned it (MISSION invariant 2). */
export function StatementBubble({ s, highlightDelay }: { s: Statement; highlightDelay?: number }) {
  const group = groupOf(s.category);
  const shape = "rounded-[14px_14px_14px_4px] border-[2.5px] px-3.5 py-2 font-mono text-[15px] leading-[1.45]";
  if (group === "real") {
    return (
      <div className="flex items-stretch gap-2.5">
        <span aria-hidden="true" className="w-1.5 shrink-0 rounded-[3px] bg-ink" />
        <div className={`relative min-w-0 flex-1 overflow-hidden border-transparent ${shape}`}>
          <span
            aria-hidden="true"
            className={`absolute inset-0 origin-left bg-real-tint ${highlightDelay !== undefined ? "motion-safe:animate-highlight" : ""}`}
            style={highlightDelay !== undefined ? { animationDelay: `${highlightDelay}ms` } : undefined}
          />
          <span className="relative">{s.quote}</span>
        </div>
      </div>
    );
  }
  return (
    <div className="flex items-stretch gap-2.5">
      <span aria-hidden="true" className="w-1.5 shrink-0" />
      <div
        className={`min-w-0 flex-1 ${shape} ${group === "polite" ? "border-dashed border-stone-grey text-muted" : "border-transparent"}`}
      >
        {s.quote}
      </div>
    </div>
  );
}

function QuoteCard({ title, quotes, empty, animate }: { title: string; quotes: Statement[]; empty: string; animate: boolean }) {
  return (
    <div className="card flex flex-col gap-4 p-6">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className={h2}>{title}</h2>
        <span className="font-mono text-sm text-muted">{quotes.length} shown</span>
      </div>
      {quotes.map((s, i) => (
        <div key={s.position} className="flex flex-col gap-1.5">
          <StatementLabel s={s} />
          <StatementBubble s={s} highlightDelay={animate ? 300 + i * 180 : undefined} />
        </div>
      ))}
      {quotes.length === 0 && <p className="m-0 text-[15px] leading-normal text-muted">{empty}</p>}
    </div>
  );
}

export function TopQuotes({ statements, animate }: { statements: Statement[]; animate: boolean }) {
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,380px),1fr))] gap-5">
      <QuoteCard title="Top real quotes" quotes={topReal(statements)} empty="No real signal in this interview yet." animate={animate} />
      <QuoteCard title="Top polite quotes" quotes={topPolite(statements)} empty="Nobody was just being nice." animate={false} />
    </div>
  );
}

const FLAG_COPY: Record<FounderFlag["key"], { title: string; bad: string; good: string }> = {
  talk_ratio: { title: "Talk time", bad: "You did most of the talking.", good: "They did most of the talking." },
  pitched_early: {
    title: "Pitched early",
    bad: "You described the product before asking about their problem.",
    good: "You asked about their problem before describing the product.",
  },
  leading_questions: {
    title: "Leading questions",
    bad: "Some of your questions suggested the answer you wanted.",
    good: "Your questions left room for a no.",
  },
};

function FlagBadge({ flag }: { flag: FounderFlag }) {
  if (flag.value === null) return <span className="tag">Not measured</span>;
  return flag.flagged ? <span className="tag tag-dark">Fix this</span> : <span className="tag">Good</span>;
}

function FlagRow({ flag }: { flag: FounderFlag }) {
  const copy = FLAG_COPY[flag.key];
  return (
    <div className="flex flex-col gap-2.5 border-t-[2.5px] border-line py-4">
      <div className="flex items-center justify-between gap-3">
        <strong className="text-base">{copy.title}</strong>
        <FlagBadge flag={flag} />
      </div>
      {flag.value === null ? (
        <span className="text-[15px] text-ink-soft">Not measured for this interview.</span>
      ) : flag.key === "talk_ratio" ? (
        <>
          <div className="relative h-3.5 overflow-hidden rounded-[7px] border-[2.5px] border-ink bg-white">
            <span className="absolute inset-y-0 left-0 bg-ink" style={{ width: percent(flag.value) }} />
          </div>
          <div className="flex justify-between gap-3 text-sm text-ink-soft">
            <span>
              You {percent(flag.value)} · them {percent(1 - flag.value)}
            </span>
            <span className="text-muted">Aim for under {percent(flag.threshold)}</span>
          </div>
        </>
      ) : (
        <>
          <span className="text-[15px] leading-normal text-ink-soft">{flag.flagged ? copy.bad : copy.good}</span>
          <span className="font-mono text-xs text-muted">
            likelihood {percent(flag.value)} · flagged at {percent(flag.threshold)}
          </span>
        </>
      )}
    </div>
  );
}

export function MistakesAndReasons({ result, positions }: { result: AnalyzeResult; positions: Set<number> }) {
  const flags = founderFlags(result);
  const toFix = flags.filter((f) => f.flagged).length;
  return (
    <div className="grid grid-cols-[repeat(auto-fit,minmax(min(100%,380px),1fr))] gap-5">
      <div className="card flex flex-col px-6 pt-6 pb-2">
        <div className="flex items-baseline justify-between gap-3 pb-3">
          <h2 className={h2}>Your mistakes</h2>
          <span className="text-sm text-muted">{toFix ? `${toFix} to fix` : "Nothing to fix"}</span>
        </div>
        {flags.map((f) => (
          <FlagRow key={f.key} flag={f} />
        ))}
      </div>
      <div className="card flex flex-col px-6 pt-6 pb-2">
        <h2 className={`${h2} mb-3`}>Why this verdict</h2>
        {result.reasons.map((text, i) => (
          <div key={i} className="flex items-start gap-3.5 border-t-[2.5px] border-line py-3.5">
            <span className="tag tag-dark shrink-0 font-mono">{i + 1}</span>
            <span className="text-base leading-normal">
              <RefText text={text} positions={positions} />
            </span>
          </div>
        ))}
        {result.reasons.length === 0 && (
          <p className="m-0 border-t-[2.5px] border-line py-3.5 text-[15px] text-muted">No reasons were written for this read-out.</p>
        )}
      </div>
    </div>
  );
}

type Copied = { target: number | "all"; ok: boolean } | null;

export function NextQuestions({ questions }: { questions: string[] }) {
  const [copied, setCopied] = useState<Copied>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(timer.current), []);

  const copy = (text: string, target: number | "all") => {
    const done = (ok: boolean) => {
      setCopied({ target, ok });
      clearTimeout(timer.current);
      timer.current = setTimeout(() => setCopied(null), 1600);
    };
    // The clipboard API is missing outside secure contexts; report that as a failed copy.
    (navigator.clipboard?.writeText(text) ?? Promise.reject()).then(
      () => done(true),
      () => done(false),
    );
  };
  const label = (target: number | "all", idle: string) =>
    copied?.target === target ? (copied.ok ? "Copied" : "Copy failed") : idle;

  return (
    <div className="card flex flex-col px-6 pt-6 pb-2">
      <div className="flex flex-wrap items-start justify-between gap-3 pb-3">
        <div className="flex flex-col gap-1">
          <h2 className={h2}>Ask these next</h2>
          <span className="text-sm text-muted">For your next interview, to get the evidence this one didn’t.</span>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => copy(questions.map((q, i) => `${i + 1}. ${q}`).join("\n"), "all")}
        >
          <span aria-live="polite">{label("all", "Copy all")}</span>
        </button>
      </div>
      {questions.map((q, i) => (
        <div key={i} className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3.5 border-t-[2.5px] border-line py-3.5">
          <span className="tag tag-dark font-mono">{i + 1}</span>
          <span className="text-[17px] leading-normal">{q}</span>
          <button type="button" className="btn btn-secondary min-w-[84px]" onClick={() => copy(q, i)}>
            <span aria-live="polite">{label(i, "Copy")}</span>
          </button>
        </div>
      ))}
    </div>
  );
}
