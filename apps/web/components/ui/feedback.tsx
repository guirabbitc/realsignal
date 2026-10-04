import Link from "next/link";

export function Notice({ title, children, tone = "plain" }: { title: string; children: React.ReactNode; tone?: "plain" | "danger" }) {
  return (
    <div
      role={tone === "danger" ? "alert" : undefined}
      className={`flex flex-col gap-2.5 rounded-[22px] border-[2.5px] bg-white p-6 ${tone === "danger" ? "border-danger" : "border-ink"}`}
    >
      <strong className={`text-[17px] ${tone === "danger" ? "text-danger" : ""}`}>{title}</strong>
      {children}
    </div>
  );
}

export function LoadFailed({ what, onRetry }: { what: string; onRetry: () => void }) {
  return (
    <Notice title={`We couldn’t load ${what}.`} tone="danger">
      <span className="text-[15px] text-ink-soft">Check your connection and try again.</span>
      <div>
        <button type="button" className="btn btn-primary" onClick={onRetry}>
          Try again
        </button>
      </div>
    </Notice>
  );
}

const bar = "rounded-[7px] bg-line motion-safe:animate-pulse-soft";

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div aria-hidden="true" className={`card flex flex-col gap-4 p-7 ${className}`}>
      <span className={`h-3.5 w-[90px] ${bar}`} />
      <div className="flex items-center gap-[18px]">
        <span className={`size-11 shrink-0 ${bar}`} />
        <span className={`h-[38px] flex-1 ${bar}`} />
        <span className={`h-[50px] w-[70px] ${bar}`} />
      </div>
      <span className={`h-3.5 w-[70%] ${bar}`} />
      <span className={`h-3.5 w-[85%] ${bar}`} />
      <span className={`h-3.5 w-[55%] ${bar}`} />
    </div>
  );
}

/** Upload → Processing → Read-out, with `current` as the 0-based active step. */
export function Steps({ current }: { current: number }) {
  return (
    <ol className="m-0 flex list-none flex-wrap items-center gap-2.5 p-0">
      {["Upload", "Processing", "Read-out"].map((label, i) => (
        <li key={label} className="flex items-center gap-2.5" aria-current={i === current ? "step" : undefined}>
          <span
            className={`flex size-[30px] items-center justify-center rounded-full border-[2.5px] border-ink text-[13px] font-extrabold ${
              i < current ? "bg-brand text-white" : i === current ? "bg-ink text-white" : "bg-white text-ink"
            }`}
          >
            {i < current ? "✓" : i + 1}
          </span>
          <span className={`text-[15px] ${i === current ? "font-bold" : "font-medium"}`}>{label}</span>
          {i < 2 && <span aria-hidden="true" className="w-7 border-t-[2.5px] border-ink" />}
        </li>
      ))}
    </ol>
  );
}

export function Breadcrumb({ ideaId, ideaText }: { ideaId?: string; ideaText?: string }) {
  return (
    <nav aria-label="Breadcrumb" className="flex flex-wrap gap-2 text-sm text-muted">
      <Link href="/ideas" className="text-muted">
        My ideas
      </Link>
      <span aria-hidden="true">/</span>
      {ideaId ? (
        <Link href={`/ideas/${ideaId}`} className="max-w-[520px] truncate text-ink">
          {ideaText ?? "Idea"}
        </Link>
      ) : (
        <span className="max-w-[520px] truncate">{ideaText ?? "Idea"}</span>
      )}
    </nav>
  );
}
