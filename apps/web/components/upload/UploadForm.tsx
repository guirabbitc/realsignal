"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { ApiError, apiPost, useApi, type IdeaDetail } from "@/components/api";
import { Breadcrumb, LoadFailed, Notice, Skeleton, Steps } from "@/components/ui/feedback";
import { TYPE_LABEL, useRunExample } from "@/components/examples/ExamplesGallery";
import { EXAMPLES, FEATURED_EXAMPLE_KEYS } from "@/lib/examples";

const FEATURED = EXAMPLES.filter((e) => FEATURED_EXAMPLE_KEYS.includes(e.key));

import { detectSpeakers, guessRoles, MAX_TRANSCRIPT_CHARS, needsMapping, relabel, type Role, type Speaker } from "./checks";

type Kind = "interview" | "demo";

const KINDS: [Kind, string][] = [
  ["interview", "Customer interview"],
  ["demo", "Demo"],
];

const ROLES: [Role, string][] = [
  ["founder", "Me"],
  ["customer", "Customer"],
  ["ignore", "Not a speaker"],
];

function WhoIsWho({
  speakers,
  roles,
  onChange,
  noCustomer,
}: {
  speakers: Speaker[];
  roles: Record<string, Role>;
  onChange: (key: string, role: Role) => void;
  noCustomer: boolean;
}) {
  return (
    <fieldset className="m-0 flex flex-col gap-3 rounded-[14px] border-[2.5px] border-ink bg-paper p-4">
      <legend className="float-left mb-1 w-full p-0">
        <strong className="block text-[15px]">Who is who?</strong>
        <span className="block text-sm leading-normal text-muted">
          We read two labels: Founder: for you and Customer: for the person you interviewed. Tell us who each of your labels is.
          We only change the labels; every word stays as written.
        </span>
      </legend>
      {speakers.map((s) => (
        <div key={s.key} className="flex flex-wrap items-center justify-between gap-2.5">
          <span className="font-mono text-sm font-bold">
            {s.label}: <span className="font-normal text-muted">{s.lines === 1 ? "1 line" : `${s.lines} lines`}</span>
          </span>
          <div role="radiogroup" aria-label={`${s.label} is`} className="inline-flex overflow-hidden rounded-xl border-[2.5px] border-ink">
            {ROLES.map(([role, label], i) => (
              <label
                key={role}
                className={`cursor-pointer px-3 py-1.5 text-sm font-bold has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-brand ${
                  i > 0 ? "border-l-[2.5px] border-ink" : ""
                } ${roles[s.key] === role ? "bg-ink text-paper" : "bg-white text-ink"}`}
              >
                <input
                  type="radio"
                  name={`role-${s.key}`}
                  value={role}
                  checked={roles[s.key] === role}
                  onChange={() => onChange(s.key, role)}
                  className="sr-only"
                />
                {label}
              </label>
            ))}
          </div>
        </div>
      ))}
      {noCustomer && (
        <p role="alert" className="m-0 text-sm leading-normal text-ink-soft">
          <strong className="text-danger">Nobody is the customer.</strong> Mark the person you interviewed as Customer, or there is
          nothing for us to judge.
        </p>
      )}
    </fieldset>
  );
}

const field = "box-border min-h-[52px] rounded-xl border-[2.5px] border-ink bg-white px-4 font-sans text-[17px] text-ink";

function sendErrorCopy(error: unknown): string {
  if (error instanceof ApiError && error.status === 422) {
    return `We couldn’t send this transcript. Check it is under ${MAX_TRANSCRIPT_CHARS.toLocaleString("en-US")} characters and try again.`;
  }
  if (error instanceof ApiError && error.status === 404) return "We couldn’t find this idea in this browser. Start again from My ideas.";
  return "We couldn’t reach valiDate. Check your connection and try again.";
}

function Form({ idea }: { idea: IdeaDetail }) {
  const router = useRouter();
  const [mode, setMode] = useState<"paste" | "file">("paste");
  const [text, setText] = useState("");
  const [fileNote, setFileNote] = useState<string | null>(null);
  const [fileError, setFileError] = useState(false);
  const [kind, setKind] = useState<Kind>("interview");
  const [who, setWho] = useState("");
  const [consent, setConsent] = useState(false);
  const [tried, setTried] = useState(false);
  const [sending, setSending] = useState(false);
  const examples = useRunExample();
  const busy = sending || examples.running !== null;
  const [sendError, setSendError] = useState<string | null>(null);
  const [roleChoices, setRoleChoices] = useState<Record<string, Role>>({});

  const hasText = text.trim().length > 0;
  const speakers = useMemo(() => detectSpeakers(text), [text]);
  const mapping = speakers.length > 0 && needsMapping(speakers);
  const roles = useMemo(() => ({ ...guessRoles(speakers), ...roleChoices }), [speakers, roleChoices]);
  const noCustomer = mapping && !speakers.some((s) => roles[s.key] === "customer");
  const unlabelled = tried && hasText && speakers.length === 0;
  const tooLong = text.length > MAX_TRANSCRIPT_CHARS;
  const ready = hasText && consent;

  async function send(payload: { transcript: string; kind: Kind; interviewee_label: string | null }) {
    setSending(true);
    setSendError(null);
    try {
      const created = await apiPost<{ id: string }>("/api/interviews", { idea_id: idea.id, ...payload });
      router.push(`/interviews/${created.id}`);
    } catch (error) {
      setSending(false);
      setSendError(sendErrorCopy(error));
    }
  }

  function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setTried(true);
    if (!ready || tooLong || speakers.length === 0 || noCustomer || busy) return;
    const transcript = mapping ? relabel(text, roles) : text;
    send({ transcript, kind, interviewee_label: who.trim() || null });
  }

  async function onFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    if (!/\.txt$/i.test(file.name) && file.type !== "text/plain") return setFileError(true);
    try {
      setText(await file.text());
      setFileNote(`${file.name} loaded. Check it below before you send it.`);
      setFileError(false);
      setTried(false);
      setMode("paste");
    } catch {
      setFileError(true);
    }
  }

  const tab = (active: boolean) =>
    `min-h-10 border-0 px-3.5 py-2 font-sans text-sm font-bold cursor-pointer ${active ? "bg-ink text-paper" : "bg-white text-ink"}`;

  return (
    <div className="flex flex-wrap items-start gap-5">
      <form onSubmit={onSubmit} noValidate className="card flex min-w-0 flex-[3_1_480px] flex-col gap-[22px] p-6">
        <div className="flex flex-col gap-2.5">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <label htmlFor="transcript" className="text-[15px] font-bold">
              Transcript
            </label>
            <div role="group" aria-label="How to add the transcript" className="inline-flex overflow-hidden rounded-xl border-[2.5px] border-ink">
              <button type="button" aria-pressed={mode === "paste"} className={tab(mode === "paste")} onClick={() => setMode("paste")}>
                Paste text
              </button>
              <button
                type="button"
                aria-pressed={mode === "file"}
                className={`${tab(mode === "file")} border-l-[2.5px] border-solid border-ink`}
                onClick={() => setMode("file")}
              >
                Upload .txt
              </button>
            </div>
          </div>

          {mode === "paste" ? (
            <textarea
              id="transcript"
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                setTried(false);
              }}
              aria-describedby="transcript-help"
              aria-invalid={unlabelled || tooLong}
              placeholder={"Founder: Walk me through the last time this happened.\nCustomer: Last month. I spent a whole Sunday on our investor update…"}
              className={`box-border min-h-[260px] w-full resize-y rounded-[14px] border-[2.5px] bg-white px-4 py-3.5 font-mono text-[15px] leading-relaxed text-ink placeholder:text-muted ${
                unlabelled || tooLong ? "border-danger" : "border-ink"
              }`}
            />
          ) : (
            <label className="relative flex cursor-pointer flex-col items-center gap-2 rounded-[14px] border-[2.5px] border-ink bg-paper px-5 py-8 text-center">
              <strong className="text-[17px]">Choose a .txt file</strong>
              <span className="text-sm text-muted">Plain text, one speaker per line. We read it in your browser.</span>
              <input id="transcript" type="file" accept=".txt,text/plain" onChange={onFile} className="absolute inset-0 cursor-pointer opacity-0" />
            </label>
          )}

          {fileNote && mode === "paste" && <span className="text-sm text-muted">{fileNote}</span>}
          {fileError && (
            <Notice title="Upload failed." tone="danger">
              <span className="text-[15px] leading-normal text-ink-soft">
                We can only read plain .txt files. Try another file, or paste the transcript as text.
              </span>
            </Notice>
          )}
          {unlabelled ? (
            <p id="transcript-help" role="alert" className="m-0 text-sm leading-normal text-ink-soft">
              <strong className="text-danger">Missing speaker labels.</strong> We can’t tell who said what. Start each line with who
              is speaking, like Founder: or Customer:
            </p>
          ) : tooLong ? (
            <p id="transcript-help" role="alert" className="m-0 text-sm leading-normal text-ink-soft">
              <strong className="text-danger">Too long.</strong> This transcript has {text.length.toLocaleString("en-US")} characters;
              the limit is {MAX_TRANSCRIPT_CHARS.toLocaleString("en-US")}. Split it into parts.
            </p>
          ) : (
            <span id="transcript-help" className="text-sm text-muted">
              Start each line with who is speaking, like Founder: or Customer:
            </span>
          )}
        </div>

        {mapping && (
          <WhoIsWho
            speakers={speakers}
            roles={roles}
            noCustomer={noCustomer}
            onChange={(key, role) => setRoleChoices((current) => ({ ...current, [key]: role }))}
          />
        )}

        <fieldset className="m-0 flex flex-col gap-2.5 border-0 p-0">
          <legend className="mb-2.5 p-0 text-[15px] font-bold">This was a</legend>
          <div className="flex flex-wrap gap-3">
            {KINDS.map(([value, label]) => (
              <label
                key={value}
                className={`flex min-h-12 cursor-pointer items-center gap-2.5 rounded-xl border-[2.5px] border-ink bg-white px-4 text-[15px] ${
                  kind === value ? "font-bold" : "font-medium"
                }`}
              >
                <input type="radio" name="kind" value={value} checked={kind === value} onChange={() => setKind(value)} className="size-5 accent-ink" />
                {label}
              </label>
            ))}
          </div>
        </fieldset>

        <div className="flex flex-col gap-2.5">
          <label htmlFor="who" className="text-[15px] font-bold">
            Who did you talk to? <span className="font-medium text-muted">(optional)</span>
          </label>
          <input
            id="who"
            type="text"
            value={who}
            maxLength={200}
            onChange={(e) => setWho(e.target.value)}
            placeholder="Sam, CEO of a 10-person B2B SaaS"
            className={field}
          />
        </div>

        <label className="flex cursor-pointer items-start gap-3 text-base leading-snug">
          <input
            type="checkbox"
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            className="mt-0.5 size-6 shrink-0 accent-brand"
          />
          <span>The interviewee knew this conversation was recorded</span>
        </label>

        <div className="flex flex-wrap items-center gap-3.5 border-t-[2.5px] border-line pt-5">
          <button
            type="submit"
            disabled={!ready || busy}
            className="btn btn-primary min-h-[52px] px-6 text-[17px] disabled:cursor-not-allowed disabled:border-stone-grey disabled:bg-line disabled:text-muted"
          >
            {sending ? "Sending…" : "Check my interview"}
          </button>
          <span className="text-sm text-muted">
            {!hasText ? "Paste or upload a transcript first." : !consent ? "Tick the consent box to continue." : "Takes up to 2 minutes."}
          </span>
        </div>
        {sendError && (
          <p role="alert" className="m-0 text-[15px] font-bold text-danger">
            {sendError}
          </p>
        )}
      </form>

      <aside className="card flex min-w-0 flex-[2_1_280px] flex-col gap-3.5 p-6">
        <h2 className="m-0 font-serif text-[26px] font-medium">Try an example</h2>
        <p className="m-0 text-[15px] leading-normal text-ink-soft">
          One click opens a made-up interview with a startup founder. Each runs under its own example idea, not this one.
        </p>
        {FEATURED.map((example) => (
          <button
            key={example.key}
            type="button"
            disabled={busy}
            onClick={() => examples.run(example)}
            className="flex min-h-[52px] cursor-pointer flex-col items-start gap-0.5 rounded-xl border-[2.5px] border-ink bg-white px-4 py-3 text-left font-sans text-ink hover:bg-line disabled:cursor-not-allowed disabled:opacity-60"
          >
            <strong className="text-base">{examples.running === example.key ? "Starting…" : TYPE_LABEL[example.type]}</strong>
            <span className="text-sm text-muted">{example.intervieweeLabel}</span>
          </button>
        ))}
        <Link href="/examples" className="text-[15px] font-bold">
          See all {EXAMPLES.length} examples
        </Link>
        {examples.error && (
          <p role="alert" className="m-0 text-sm font-bold text-danger">
            {examples.error}
          </p>
        )}
        <div className="flex flex-col gap-1.5 border-t-[2.5px] border-line pt-3.5">
          <span className="text-[13px] font-bold text-muted">What we need</span>
          <span className="font-mono text-sm leading-relaxed">
            <strong>Founder:</strong> How do you do this today?
            <br />
            <strong>Customer:</strong> I export it from Stripe and fix it in a spreadsheet.
          </span>
        </div>
      </aside>
    </div>
  );
}

export function UploadForm({ ideaId }: { ideaId: string }) {
  const { load, retry } = useApi<IdeaDetail>(`/api/ideas/${ideaId}`);

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

  return (
    <section aria-label="Add an interview" className="flex flex-col gap-6">
      <Breadcrumb ideaId={ideaId} ideaText={load.state === "ready" ? load.data.one_liner : undefined} />
      <div className="flex flex-wrap items-end justify-between gap-5">
        <h1 className="m-0 font-serif text-[clamp(34px,4.4vw,52px)] leading-[1.05] font-medium tracking-[-0.02em]">Add an interview</h1>
        <Steps current={0} />
      </div>
      {load.state === "ready" ? <Form idea={load.data} /> : <Skeleton />}
    </section>
  );
}
