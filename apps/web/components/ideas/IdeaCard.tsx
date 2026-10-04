import Link from "next/link";

import type { IdeaSummary } from "@/components/api";
import { VERDICT_LABEL, VERDICT_STONE } from "@/components/read-out/view-model";
import { Stone } from "@/components/ui/Stone";

// GET /api/ideas returns the latest verdict but not its score, so the card shows the verdict only.
export function IdeaCard({ idea }: { idea: IdeaSummary }) {
  const count = idea.interview_count;
  return (
    <Link
      href={`/ideas/${idea.id}`}
      className="card flex flex-col gap-3.5 px-6 py-[22px] text-ink no-underline hover:bg-white hover:text-ink hover:shadow-[4px_4px_0_var(--color-ink)]"
    >
      <span className="font-serif text-[23px] leading-[1.15] font-medium text-pretty">{idea.one_liner}</span>
      {idea.latest_verdict ? (
        <span className="flex items-center gap-3">
          <Stone kind={VERDICT_STONE[idea.latest_verdict]} size={30} />
          <span className="font-serif text-lg leading-tight">{VERDICT_LABEL[idea.latest_verdict]}</span>
        </span>
      ) : (
        <span className="text-[15px] text-muted">No read-outs yet.</span>
      )}
      <span className="mt-auto border-t-[2.5px] border-line pt-3 text-sm text-muted">
        {count === 1 ? "1 interview" : `${count} interviews`}
      </span>
    </Link>
  );
}

export function IdeaGrid({ children }: { children: React.ReactNode }) {
  return <div className="grid grid-cols-[repeat(auto-fill,minmax(min(100%,300px),1fr))] gap-5">{children}</div>;
}
