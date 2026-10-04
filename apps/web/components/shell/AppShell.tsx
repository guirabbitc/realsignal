"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { ChatWidget } from "@/components/chat/ChatWidget";
import { Stone } from "@/components/ui/Stone";

import { CurrentIdeaContext } from "./current-idea";

interface IdeaRow {
  id: string;
  one_liner: string;
  interview_count: number;
}

function Logo({ size }: { size: "lg" | "sm" }) {
  return (
    <Link href="/" className="flex items-center gap-2.5 px-1.5 text-ink no-underline hover:text-ink">
      <Stone kind="real" size={size === "lg" ? 30 : 26} />
      <span className={`font-serif font-medium tracking-[-0.02em] ${size === "lg" ? "text-[26px]" : "text-[22px]"}`}>
        valiDate
      </span>
    </Link>
  );
}

function NavItem({ href, label, count, active }: { href: string; label: string; count?: string; active: boolean }) {
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={`flex min-h-10 items-center justify-between gap-2.5 rounded-xl border-[2.5px] px-3 py-2 text-[15px] text-ink no-underline hover:bg-white hover:text-ink ${
        active ? "border-ink bg-white font-bold" : "border-transparent font-medium"
      }`}
    >
      <span className="min-w-0 truncate">{label}</span>
      {count !== undefined && <span className="shrink-0 font-mono text-[13px] text-muted">{count}</span>}
    </Link>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [ideas, setIdeas] = useState<IdeaRow[] | null>(null);
  const [reportedIdea, setReportedIdea] = useState<string | null>(null);
  const report = useCallback((ideaId: string | null) => setReportedIdea(ideaId), []);

  // Refetch on navigation so interview counts stay current after an upload.
  useEffect(() => {
    let cancelled = false;
    fetch("/api/ideas")
      .then((r) => (r.ok ? r.json() : { ideas: [] }))
      .then((body: { ideas: IdeaRow[] }) => !cancelled && setIdeas(body.ideas))
      .catch(() => !cancelled && setIdeas([]));
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  const ideaInPath = pathname.match(/^\/ideas\/([^/]+)/)?.[1] ?? null;
  const currentId = ideaInPath ?? reportedIdea;
  const current = ideas?.find((i) => i.id === currentId) ?? null;

  return (
    <CurrentIdeaContext value={report}>
      <div className="flex min-h-screen flex-col wide:flex-row">
        <aside className="sticky top-0 hidden h-screen w-[272px] shrink-0 flex-col gap-[22px] overflow-y-auto border-r-[2.5px] border-ink px-[18px] py-6 wide:flex">
          <Logo size="lg" />
          <Link href="/" className="btn btn-primary min-h-11">
            New idea
          </Link>
          <nav aria-label="Main" className="flex flex-col gap-1">
            <NavItem href="/" label="Home" active={pathname === "/"} />
            <NavItem href="/ideas" label="My ideas" count={ideas ? String(ideas.length) : ""} active={pathname === "/ideas"} />
            <NavItem href="/chat" label="Chat with the agents" active={pathname === "/chat"} />
          </nav>
          <nav aria-label="Ideas" className="flex flex-col gap-1.5">
            <span className="px-3 text-[13px] font-bold text-muted">Ideas</span>
            {ideas?.map((idea) => (
              <NavItem
                key={idea.id}
                href={`/ideas/${idea.id}`}
                label={idea.one_liner}
                count={String(idea.interview_count)}
                active={idea.id === currentId}
              />
            ))}
            {ideas?.length === 0 && <span className="px-3 text-sm text-muted">No ideas yet.</span>}
          </nav>
          {current && (
            <nav aria-label="This idea" className="flex flex-col gap-1.5">
              <span className="px-3 text-[13px] font-bold text-muted">This idea</span>
              <NavItem
                href={`/ideas/${current.id}`}
                label="Interviews"
                count={String(current.interview_count)}
                active={pathname === `/ideas/${current.id}`}
              />
              <NavItem
                href={`/ideas/${current.id}/upload`}
                label="Analyze an interview"
                active={pathname === `/ideas/${current.id}/upload`}
              />
            </nav>
          )}
        </aside>

        <header className="sticky top-0 z-10 flex items-center justify-between gap-3 border-b-[2.5px] border-ink bg-paper px-5 py-3 wide:hidden">
          <Logo size="sm" />
          <div className="flex items-center gap-3.5">
            <Link href="/ideas" className="text-[15px] font-bold text-ink">
              My ideas
            </Link>
            <Link href="/chat" className="text-[15px] font-bold text-ink">
              Chat
            </Link>
            <Link href="/" className="btn btn-primary">
              New idea
            </Link>
          </div>
        </header>

        <main className="min-w-0 flex-1 px-5 pt-6 pb-16 wide:px-12 wide:pt-10 wide:pb-24">
          <div className="mx-auto flex max-w-[1040px] flex-col gap-7">{children}</div>
        </main>
        {/* The chat page is the same conversation at full size. */}
        {pathname !== "/chat" && <ChatWidget />}
      </div>
    </CurrentIdeaContext>
  );
}
