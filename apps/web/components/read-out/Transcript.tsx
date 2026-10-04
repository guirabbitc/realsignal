import type { Statement } from "@/lib/contracts";

import { StatementBubble } from "./Sections";
import { CATEGORY_LABEL, groupOf, percent, rebuildTranscript } from "./view-model";

export function Transcript({ statements, customerName }: { statements: Statement[]; customerName: string }) {
  const turns = rebuildTranscript(statements);
  return (
    <div className="card flex flex-col px-6 pt-6 pb-2">
      <div className="flex flex-wrap items-baseline justify-between gap-3 pb-3">
        <h2 className="m-0 font-serif text-[26px] font-medium">Transcript</h2>
        <span className="text-sm text-muted">
          {statements.length} customer {statements.length === 1 ? "sentence" : "sentences"}, each one marked
        </span>
      </div>
      {turns.map((turn) => (
        <div
          key={turn.key}
          className="grid grid-cols-[minmax(0,1fr)] items-start gap-x-4 gap-y-1.5 border-t-[2.5px] border-line py-3 min-[560px]:grid-cols-[72px_minmax(0,1fr)]"
        >
          <span
            className={`truncate pt-[3px] font-mono text-[13px] font-bold ${turn.speaker === "founder" ? "text-muted" : "text-ink"}`}
          >
            {turn.speaker === "founder" ? "YOU" : customerName}
          </span>
          {turn.speaker === "founder" ? (
            <span className="text-base leading-relaxed text-ink-soft">{turn.text}</span>
          ) : (
            <div className="flex flex-col gap-3">
              {turn.statements.map((s) => (
                <div key={s.position} id={`line-${s.position}`} className="flex scroll-mt-24 flex-col gap-[5px]">
                  <div className="flex flex-wrap items-baseline gap-2.5">
                    <span className={`text-[13px] font-bold ${groupOf(s.category) === "real" ? "text-brand" : "text-muted"}`}>
                      {CATEGORY_LABEL[s.category]}
                    </span>
                    <span className="font-mono text-xs text-muted">
                      #{s.position} · real signal {percent(s.p_real)}
                    </span>
                  </div>
                  <StatementBubble s={s} />
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
      {statements.length === 0 && (
        <p className="m-0 border-t-[2.5px] border-line py-3.5 text-[15px] text-muted">
          The customer didn’t say anything we could judge.
        </p>
      )}
    </div>
  );
}
