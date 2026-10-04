"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { apiGet, apiPost, type IdeaDetail } from "@/components/api";
import { useReportCurrentIdea } from "@/components/shell/current-idea";
import { Breadcrumb, LoadFailed, Notice, Skeleton, Steps } from "@/components/ui/feedback";

import { SavedTranscript } from "./SavedTranscript";
import { MissingEvidence, MistakesAndReasons, NextQuestions, TopQuotes, VerdictCard } from "./Sections";
import { Transcript } from "./Transcript";
import { errorMessage, shortDate, type InterviewResponse } from "./view-model";

const POLL_MS = 2000;
const MAX_FETCH_FAILURES = 3;

type Load =
  | { state: "loading" }
  | { state: "missing" }
  | { state: "error" }
  // `fresh`: this view saw the interview go from processing to done, so the reveal animates.
  | { state: "ready"; interview: InterviewResponse; fresh: boolean };

const PIPELINE = [
  ["Who said what", "Splitting the transcript into your lines and theirs."],
  ["Real or polite", "Judging every sentence the customer said."],
  ["Your questions", "Checking talk time, pitching and leading questions."],
  ["The verdict", "Scoring the evidence and writing the read-out."],
] as const;

function Processing() {
  return (
    <>
      <div aria-live="polite" className="card flex flex-col gap-5 p-6">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h2 className="m-0 font-serif text-[30px] font-medium">Reading your interview.</h2>
          <span className="text-sm text-muted">Checking every 2 seconds. This can take up to 2 minutes.</span>
        </div>
        <ol className="m-0 grid list-none grid-cols-[repeat(auto-fit,minmax(min(100%,190px),1fr))] gap-3.5 p-0">
          {PIPELINE.map(([title, task], i) => (
            <li key={title} className="flex flex-col gap-2 rounded-[18px] border-[2.5px] border-ink bg-paper p-3.5">
              <span className="font-mono text-[13px] font-bold text-muted">{i + 1}</span>
              <strong className="font-serif text-[22px] font-medium">{title}</strong>
              <span className="text-sm leading-snug text-ink-soft">{task}</span>
            </li>
          ))}
        </ol>
      </div>
      <Skeleton />
    </>
  );
}

export function ReadOut({ id }: { id: string }) {
  const [load, setLoad] = useState<Load>({ state: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [idea, setIdea] = useState<IdeaDetail | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [retryError, setRetryError] = useState<string | null>(null);

  /** Analyzes the saved transcript again, then polls like a new interview. */
  async function retry() {
    setRetrying(true);
    setRetryError(null);
    try {
      await apiPost(`/api/interviews/${id}/retry`, {});
      setLoad({ state: "loading" });
      setAttempt((a) => a + 1);
    } catch {
      setRetryError("We couldn’t start the analysis again. Check your connection and try again.");
    } finally {
      setRetrying(false);
    }
  }

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let failures = 0;
    let lastStatus: string | null = null;

    const poll = async () => {
      try {
        const res = await fetch(`/api/interviews/${id}`, { cache: "no-store" });
        if (cancelled) return;
        if (res.status === 404) return setLoad({ state: "missing" });
        if (!res.ok) throw new Error(`status ${res.status}`);
        const interview = (await res.json()) as InterviewResponse;
        if (cancelled) return;
        failures = 0;
        setLoad({ state: "ready", interview, fresh: lastStatus === "processing" && interview.status === "done" });
        lastStatus = interview.status;
        if (interview.status === "processing") timer = setTimeout(poll, POLL_MS);
      } catch {
        if (cancelled) return;
        failures += 1;
        if (failures < MAX_FETCH_FAILURES) timer = setTimeout(poll, POLL_MS);
        else setLoad({ state: "error" });
      }
    };
    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [id, attempt]);

  const ideaId = load.state === "ready" ? load.interview.idea_id : null;
  useReportCurrentIdea(ideaId);

  // The interview endpoint has no label, kind or date; the idea's history does.
  useEffect(() => {
    if (!ideaId) return;
    let cancelled = false;
    apiGet<IdeaDetail>(`/api/ideas/${ideaId}`).then(
      (body) => !cancelled && setIdea(body),
      () => {},
    );
    return () => {
      cancelled = true;
    };
  }, [ideaId]);

  const result = load.state === "ready" ? load.interview.result : null;
  const positions = useMemo(() => new Set(result?.statements.map((s) => s.position)), [result]);

  if (load.state === "loading") return <Skeleton />;
  if (load.state === "missing") {
    return (
      <Notice title="We can’t find that interview.">
        <span className="text-[15px] text-ink-soft">Check the link, or open it in the browser you used to add it.</span>
        <Link href="/ideas" className="text-[15px] font-bold">
          Go to my ideas
        </Link>
      </Notice>
    );
  }
  if (load.state === "error") {
    return (
      <LoadFailed
        what="this interview"
        onRetry={() => {
          setLoad({ state: "loading" });
          setAttempt((a) => a + 1);
        }}
      />
    );
  }

  const { interview, fresh } = load;
  const row = idea?.interviews.find((i) => i.id === interview.id);
  const label = row?.interviewee_label?.trim();
  const customerName = label ? label.split(",")[0].trim().toUpperCase() : "THEM";
  const ideaHref = `/ideas/${interview.idea_id}`;
  const uploadHref = `${ideaHref}/upload`;
  const done = interview.status === "done" && result !== null;
  const failed = interview.status === "failed" || (interview.status === "done" && result === null);

  return (
    <section aria-label="Read-out" className="flex flex-col gap-6">
      <Breadcrumb ideaId={interview.idea_id} ideaText={idea?.one_liner} />

      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex min-w-0 flex-col gap-2">
          <h1 className="m-0 font-serif text-[clamp(30px,3.8vw,44px)] leading-[1.08] font-medium tracking-[-0.02em]">
            {label || "Interview"}
          </h1>
          {row && (
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="tag">{row.kind === "demo" ? "Demo" : "Interview"}</span>
              <span className="font-mono text-[13px] text-muted">{shortDate(row.created_at)}</span>
            </div>
          )}
        </div>
        {done && (
          <Link href={uploadHref} className="btn btn-secondary min-h-[52px] px-5 text-base">
            Analyze another interview
          </Link>
        )}
        {interview.status === "processing" && <Steps current={1} />}
      </div>

      {interview.status === "processing" && <Processing />}

      {failed && (
        <Notice title="Analysis failed." tone="danger">
          <span className="text-[15px] leading-normal text-ink-soft">{errorMessage(interview.error)}</span>
          {interview.error && <span className="font-mono text-[13px] text-muted">Error code: {interview.error}</span>}
          <div className="mt-1.5 flex flex-wrap gap-2.5">
            {interview.status === "failed" && (
              <button type="button" className="btn btn-primary disabled:cursor-not-allowed disabled:opacity-60" disabled={retrying} onClick={retry}>
                {retrying ? "Starting…" : "Try again"}
              </button>
            )}
            <Link href={uploadHref} className={`btn ${interview.status === "failed" ? "btn-secondary" : "btn-primary"}`}>
              Add the interview again
            </Link>
            <Link href={ideaHref} className="btn btn-secondary">
              Back to the idea
            </Link>
          </div>
          {retryError && (
            <p role="alert" className="m-0 text-[15px] font-bold text-danger">
              {retryError}
            </p>
          )}
        </Notice>
      )}

      {failed && interview.transcript && <SavedTranscript text={interview.transcript} />}

      {done && (
        <>
          {result.statements.length === 0 && (
            <Notice title="We found no customer lines in this transcript.">
              <span className="text-[15px] leading-normal text-ink-soft">
                We judge the lines that start with Customer:. This transcript had none, so every line was counted as yours. If you
                labelled the speakers another way, like Interviewer: or a name, add it again and tell us who is who.
              </span>
              <div>
                <Link href={uploadHref} className="btn btn-primary">
                  Add the interview again
                </Link>
              </div>
            </Notice>
          )}
          <VerdictCard result={result} animate={fresh} positions={positions} />
          {result.verdict === "need_more_evidence" && <MissingEvidence text={result.missing_evidence} />}
          <TopQuotes statements={result.statements} animate={fresh} />
          <MistakesAndReasons result={result} positions={positions} />
          <NextQuestions questions={result.next_questions} />
          <Transcript statements={result.statements} customerName={customerName} />
        </>
      )}
    </section>
  );
}
