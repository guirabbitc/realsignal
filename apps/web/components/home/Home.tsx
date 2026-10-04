"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError, apiPost, useApi, type IdeaSummary } from "@/components/api";
import { IdeaCard, IdeaGrid } from "@/components/ideas/IdeaCard";

const MAX_IDEA_CHARS = 500;

export function Home() {
  const router = useRouter();
  const { load, retry } = useApi<{ ideas: IdeaSummary[] }>("/api/ideas");
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const ready = draft.trim().length > 0;

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!ready || sending) return;
    setSending(true);
    setError(null);
    try {
      const idea = await apiPost<{ id: string }>("/api/ideas", { one_liner: draft.trim().replace(/\s+/g, " ") });
      router.push(`/ideas/${idea.id}/upload`);
    } catch (err) {
      setSending(false);
      setError(
        err instanceof ApiError && err.status === 422
          ? `Write your idea in one sentence, up to ${MAX_IDEA_CHARS} characters.`
          : "We couldn’t reach valiDate. Check your connection and try again.",
      );
    }
  }

  const ideas = load.state === "ready" ? load.data.ideas : [];

  return (
    <section aria-label="Home" className="flex flex-col gap-8">
      <div className="flex flex-col gap-5 pt-4">
        <h1 className="m-0 font-serif text-[clamp(42px,6vw,84px)] leading-[1.03] font-normal tracking-[-0.025em]">
          They said they love it.
          <br />
          <em className="text-muted">Are they really into you?</em>
        </h1>
        <p className="m-0 max-w-[560px] text-[19px] leading-normal text-pretty text-ink-soft">
          Paste a customer interview. We line up everything they said and show you what was real and what was just being nice.
        </p>
      </div>

      <form onSubmit={onSubmit} className="card flex flex-col gap-3 p-6">
        <label htmlFor="idea-input" className="text-[15px] font-bold">
          Describe your idea in one sentence
        </label>
        <div className="flex flex-wrap gap-3">
          <input
            id="idea-input"
            type="text"
            value={draft}
            maxLength={MAX_IDEA_CHARS}
            onChange={(e) => setDraft(e.target.value)}
            placeholder="Automated SOC 2 evidence collection for seed-stage SaaS startups."
            className="box-border min-h-[52px] min-w-0 flex-[1_1_320px] rounded-xl border-[2.5px] border-ink bg-white px-4 font-sans text-[17px] text-ink placeholder:text-muted"
          />
          <button
            type="submit"
            disabled={!ready || sending}
            className="btn btn-primary min-h-[52px] px-6 text-[17px] disabled:cursor-not-allowed disabled:border-stone-grey disabled:bg-line disabled:text-muted"
          >
            {sending ? "Creating…" : "Next: add an interview"}
          </button>
        </div>
        <span className="text-sm text-muted">One idea, one sentence. Add as many interviews to it as you like.</span>
        {error && (
          <p role="alert" className="m-0 text-[15px] font-bold text-danger">
            {error}
          </p>
        )}
      </form>

      {ideas.length > 0 && (
        <div className="flex flex-col gap-4">
          <div className="flex items-baseline justify-between gap-4">
            <h2 className="m-0 font-serif text-[32px] font-medium">Your ideas</h2>
            <Link href="/ideas" className="text-[15px] font-bold">
              See all
            </Link>
          </div>
          <IdeaGrid>
            {ideas.slice(0, 3).map((idea) => (
              <IdeaCard key={idea.id} idea={idea} />
            ))}
          </IdeaGrid>
        </div>
      )}
      {load.state === "error" && (
        <p className="m-0 text-[15px] text-ink-soft">
          We couldn’t load your ideas.{" "}
          <button type="button" onClick={retry} className="cursor-pointer border-0 bg-transparent p-0 font-sans text-[15px] font-bold text-brand underline">
            Try again
          </button>
        </p>
      )}
    </section>
  );
}
