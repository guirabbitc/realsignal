"use client";

import { createContext, useContext, useEffect } from "react";

// Pages whose URL does not name the idea (the read-out) report it here, so the sidebar can show "This idea".
export const CurrentIdeaContext = createContext<(ideaId: string | null) => void>(() => {});

export function useReportCurrentIdea(ideaId: string | null | undefined) {
  const report = useContext(CurrentIdeaContext);
  useEffect(() => {
    report(ideaId ?? null);
    return () => report(null);
  }, [ideaId, report]);
}
