"use client";

import Link from "next/link";

import { useApi, type IdeaSummary } from "@/components/api";
import { LoadFailed } from "@/components/ui/feedback";
import { Stone } from "@/components/ui/Stone";

import { IdeaCard, IdeaGrid } from "./IdeaCard";

function CardSkeleton() {
  return (
    <div aria-hidden="true" className="card flex h-[190px] flex-col gap-3.5 px-6 py-[22px]">
      <span className="h-5 w-[85%] rounded-[7px] bg-line motion-safe:animate-pulse-soft" />
      <span className="h-5 w-[60%] rounded-[7px] bg-line motion-safe:animate-pulse-soft" />
      <span className="mt-auto h-3.5 w-[40%] rounded-[7px] bg-line motion-safe:animate-pulse-soft" />
    </div>
  );
}

export function IdeasList() {
  const { load, retry } = useApi<{ ideas: IdeaSummary[] }>("/api/ideas");

  return (
    <section aria-label="My ideas" className="flex flex-col gap-7">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1.5">
          <h1 className="m-0 font-serif text-[clamp(34px,4.4vw,52px)] leading-[1.05] font-medium tracking-[-0.02em]">My ideas</h1>
          <span className="text-base text-ink-soft">The latest verdict for each idea.</span>
        </div>
        <Link href="/" className="btn btn-primary min-h-[52px] px-6 text-[17px]">
          New idea
        </Link>
      </div>

      {load.state === "loading" && (
        <IdeaGrid>
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </IdeaGrid>
      )}
      {(load.state === "error" || load.state === "missing") && <LoadFailed what="your ideas" onRetry={retry} />}
      {load.state === "ready" && load.data.ideas.length === 0 && (
        <div className="card flex flex-col items-center gap-3.5 px-6 py-10 text-center">
          <Stone kind="unsure" size={64} />
          <p className="m-0 font-serif text-[32px] font-medium">No ideas yet.</p>
          <p className="m-0 text-[17px] leading-normal text-ink-soft">Write it in one sentence and we’ll take it from there.</p>
          <Link href="/" className="btn btn-primary min-h-[52px] px-6 text-[17px]">
            Describe my idea
          </Link>
        </div>
      )}
      {load.state === "ready" && load.data.ideas.length > 0 && (
        <IdeaGrid>
          {load.data.ideas.map((idea) => (
            <IdeaCard key={idea.id} idea={idea} />
          ))}
        </IdeaGrid>
      )}
    </section>
  );
}
