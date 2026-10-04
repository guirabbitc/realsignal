"use client";

import Link from "next/link";
import { useEffect } from "react";

import { useApi, type IdeaDetail, type IdeaInterviewRow } from "@/components/api";
import { shortDate, VERDICT_LABEL, VERDICT_STONE } from "@/components/read-out/view-model";
import { Breadcrumb, LoadFailed, Notice, Skeleton } from "@/components/ui/feedback";
import { Stone } from "@/components/ui/Stone";
import { isExampleIdea } from "@/lib/examples";

import { barHeight, readOuts, shortName, STALE_PROCESSING_MS, trendCaption, type ReadOutRow } from "./history";

const REFRESH_MS = 3000;
const h2 = "m-0 font-serif text-[26px] font-medium";
const linkReset = "text-ink no-underline hover:text-ink";

function ScoreChart({ done }: { done: ReadOutRow[] }) {
  return (
    <div className="card flex min-w-0 flex-[2_1_420px] flex-col gap-[18px] p-6">
      <div className="flex flex-wrap items-baseline justify-between gap-3">
        <h2 className={h2}>Score across interviews</h2>
        <span className="text-sm text-muted">{trendCaption(done)}</span>
      </div>
      {done.length === 0 ? (
        <p className="m-0 text-[15px] text-muted">Scores show up here when a read-out is ready.</p>
      ) : (
        <>
          <ol aria-label="Scores, oldest first" className="m-0 flex h-[210px] list-none items-end gap-3.5 border-b-[2.5px] border-ink px-1 py-0">
            {done.map((r, i) => (
              <li key={r.id} className="flex max-w-[84px] min-w-0 flex-1">
                <Link
                  href={`/interviews/${r.id}`}
                  aria-label={`#${i + 1} ${shortName(r.interviewee_label)}: ${VERDICT_LABEL[r.verdict]}, score ${r.score ?? "none"}`}
                  className={`flex w-full flex-col items-center gap-1.5 ${linkReset}`}
                >
                  <span className="font-mono text-[17px] font-bold">{r.score ?? "—"}</span>
                  <span
                    className="box-border flex w-full justify-center rounded-t-[10px] border-[2.5px] border-b-0 border-ink bg-white pt-2"
                    style={{ height: barHeight(r.score) }}
                  >
                    <Stone kind={VERDICT_STONE[r.verdict]} size={24} />
                  </span>
                </Link>
              </li>
            ))}
          </ol>
          <div aria-hidden="true" className="flex gap-3.5 px-1">
            {done.map((r, i) => (
              <span key={r.id} className="max-w-[84px] min-w-0 flex-1 truncate text-center text-xs text-muted">
                #{i + 1} {shortName(r.interviewee_label)}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function LatestVerdict({ latest }: { latest: ReadOutRow }) {
  return (
    <Link href={`/interviews/${latest.id}`} className={`card flex min-w-0 flex-[1_1_260px] flex-col gap-4 p-6 ${linkReset}`}>
      <span className="text-[13px] font-bold text-muted">Latest verdict · {shortName(latest.interviewee_label)}</span>
      <Stone kind={VERDICT_STONE[latest.verdict]} size={44} />
      <span className="font-serif text-[30px] leading-[1.08] font-medium tracking-[-0.01em]">{VERDICT_LABEL[latest.verdict]}</span>
      <span className="mt-auto flex items-baseline justify-between border-t-[2.5px] border-line pt-3.5">
        <span className="text-[15px] font-bold text-brand">Open the read-out</span>
        <span className="font-mono text-[30px] font-bold">{latest.score ?? "—"}</span>
      </span>
    </Link>
  );
}

function rowLine(r: IdeaInterviewRow): string {
  if (r.status === "done" && r.verdict) return VERDICT_LABEL[r.verdict];
  if (r.status === "failed") return "Analysis failed. Open it to see why.";
  return "Reading…";
}

function InterviewRows({ rows }: { rows: IdeaInterviewRow[] }) {
  return (
    <div className="card flex flex-col px-6 pt-[22px] pb-2">
      <div className="flex items-baseline justify-between pb-3">
        <h2 className={h2}>Interviews</h2>
        <span className="font-mono text-sm text-muted">{rows.length}</span>
      </div>
      {rows.map((r) => (
        <Link
          key={r.id}
          href={`/interviews/${r.id}`}
          className={`grid grid-cols-[34px_minmax(0,1fr)_auto] items-center gap-4 border-t-[2.5px] border-line py-4 ${linkReset}`}
        >
          <span className="flex">{r.verdict && <Stone kind={VERDICT_STONE[r.verdict]} size={32} />}</span>
          <span className="flex min-w-0 flex-col gap-1">
            <span className="flex flex-wrap items-baseline gap-2.5">
              <strong className="text-base">{r.interviewee_label || "Untitled interview"}</strong>
              <span className="font-mono text-[13px] text-muted">
                {shortDate(r.created_at)} · {r.kind === "demo" ? "Demo" : "Interview"}
              </span>
            </span>
            <span className={`font-serif text-[19px] leading-tight ${r.status === "failed" ? "text-danger" : ""}`}>{rowLine(r)}</span>
          </span>
          <span className="flex items-center">
            {r.status === "done" && <span className="font-mono text-[26px] font-bold">{r.score ?? "—"}</span>}
            {r.status === "failed" && <span className="rounded bg-danger px-2.5 py-1 text-[13px] font-bold text-white">Failed</span>}
            {r.status === "processing" && <span className="tag">Reading…</span>}
          </span>
        </Link>
      ))}
    </div>
  );
}

export function IdeaHistory({ ideaId }: { ideaId: string }) {
  const { load, refresh, retry } = useApi<IdeaDetail>(`/api/ideas/${ideaId}`);
  const uploadHref = `/ideas/${ideaId}/upload`;

  // Keep the list current while a recent analysis is still running.
  useEffect(() => {
    if (load.state !== "ready") return;
    const running = load.data.interviews.some(
      (r) => r.status === "processing" && Date.now() - Date.parse(r.created_at) < STALE_PROCESSING_MS,
    );
    if (!running) return;
    const timer = setTimeout(refresh, REFRESH_MS);
    return () => clearTimeout(timer);
  }, [load, refresh]);

  if (load.state === "missing") {
    return (
      <Notice title="We can’t find that idea.">
        <span className="text-[15px] text-ink-soft">Check the link, or open it in the browser you used to create it.</span>
        <Link href="/ideas" className="text-[15px] font-bold">
          Go to my ideas
        </Link>
      </Notice>
    );
  }
  if (load.state === "error") return <LoadFailed what="this idea" onRetry={retry} />;
  if (load.state === "loading") {
    return (
      <section aria-label="Idea history" className="flex flex-col gap-6">
        <Breadcrumb />
        <Skeleton />
      </section>
    );
  }

  const idea = load.data;
  const done = readOuts(idea.interviews);
  const latest = done[done.length - 1];

  return (
    <section aria-label="Idea history" className="flex flex-col gap-6">
      <Breadcrumb />
      {isExampleIdea(idea.one_liner) && (
        <p className="m-0 text-sm text-muted">
          <span className="tag mr-2">Example</span>
          This idea holds the example interviews you ran. <Link href="/examples">See all examples</Link>
        </p>
      )}
      <div className="flex flex-wrap items-end justify-between gap-5">
        <h1 className="m-0 flex-[1_1_420px] font-serif text-[clamp(30px,3.8vw,46px)] leading-[1.08] font-medium tracking-[-0.02em] text-balance">
          {idea.one_liner}
        </h1>
        {idea.interviews.length > 0 && (
          <Link href={uploadHref} className="btn btn-primary min-h-[52px] px-6 text-[17px]">
            Analyze another interview
          </Link>
        )}
      </div>

      {idea.interviews.length === 0 ? (
        <div className="card flex flex-col items-center gap-4 rounded-[26px] px-6 py-10 text-center">
          <Stone kind="unsure" size={64} />
          <p className="m-0 font-serif text-[34px] leading-[1.1] font-medium">No interviews yet.</p>
          <p className="m-0 max-w-[380px] text-[17px] leading-normal text-ink-soft">
            Talk to a few customers. Paste the first transcript when you’re back and we’ll show you what was real.
          </p>
          <Link href={uploadHref} className="btn btn-primary min-h-[52px] px-6 text-[17px]">
            Add my first interview
          </Link>
        </div>
      ) : (
        <>
          <div className="flex flex-wrap gap-5">
            <ScoreChart done={done} />
            {latest && <LatestVerdict latest={latest} />}
          </div>
          <InterviewRows rows={idea.interviews} />
        </>
      )}
    </section>
  );
}
