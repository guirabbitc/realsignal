import type { StoneKind } from "@/components/read-out/view-model";

const FILL: Record<StoneKind, string> = { real: "#0F9D5C", polite: "#8E9096", unsure: "#FFFFFF" };

/** The valiDate diamond: solid green for a real-signal verdict, grey for polite, dashed for unsure. */
export function Stone({ kind, size }: { kind: StoneKind; size: number }) {
  return (
    <svg viewBox="0 0 40 40" width={size} height={size} aria-hidden="true" className="shrink-0">
      <rect
        x="11"
        y="11"
        width="18"
        height="18"
        rx="3"
        transform="rotate(45 20 20)"
        fill={FILL[kind]}
        stroke="#16181D"
        strokeWidth="3.5"
        strokeDasharray={kind === "unsure" ? "5 3.5" : undefined}
      />
    </svg>
  );
}
