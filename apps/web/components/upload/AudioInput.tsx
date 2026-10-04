"use client";

// Record or upload an interview, have it transcribed, and let the founder say which voice is theirs.
// What comes out is a plain Founder:/Customer: transcript handed back to the form, which sends it like pasted
// text. The audio never leaves this tab except for the one transcription request, and nothing keeps it.
import { useState } from "react";

import { audioExtension } from "@/lib/audio-config";
import type { TranscribeResult } from "@/lib/contracts";

import { buildTranscript } from "./transcript-builder";
import { extensionFor, useRecorder, type RecorderState } from "./useRecorder";

export interface AudioLimits {
  maxMb: number;
  maxMinutes: number;
}

interface Pending {
  blob: Blob;
  name: string;
  seconds: number | null;
}

type Flow =
  | { step: "capture" }
  | { step: "sending"; pending: Pending; phase: "uploading" | "transcribing" }
  | { step: "review"; result: TranscribeResult; founderId: string }
  | { step: "failed"; message: string };

type Outcome = { ok: true; result: TranscribeResult } | { ok: false; code: string; reason: string | null };

const WARN_BEFORE_END_S = 5 * 60;
const PEOPLE = [2, 3, 4];
const FORMATS = "MP3, M4A, WAV, WebM, OGG or MP4";

export function clock(seconds: number): string {
  const total = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const rest = String(total % 60).padStart(2, "0");
  return hours ? `${hours}:${String(minutes).padStart(2, "0")}:${rest}` : `${minutes}:${rest}`;
}

export function fileSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function transcribingCopy(seconds: number | null): string {
  if (seconds === null) return "Transcribing your audio. This can take a minute.";
  if (seconds < 60) return "Transcribing less than a minute of audio. This can take a moment.";
  const minutes = Math.round(seconds / 60);
  return `Transcribing ${minutes} ${minutes === 1 ? "minute" : "minutes"} of audio. This can take a minute.`;
}

function failureCopy(code: string, reason: string | null, maxMb: number): string {
  if (code === "audio_too_large") return `This audio is over ${maxMb} MB. Export it as .m4a or .mp3, or split it, and try again.`;
  if (code === "empty_audio") return "We couldn’t read any audio in this file. Check that it plays, then try again.";
  if (code === "no_speech") return "We couldn’t hear anyone speaking. Check that the right file or microphone was used.";
  if (code === "consent_required") return "Tick the consent box first.";
  if (code === "network") return "We couldn’t reach valiDate. Check your connection and try again.";
  if (code === "http_404") return "We couldn’t find this idea in this browser. Start again from My ideas.";
  if (reason === "rate_limited") return "Our transcription provider is busy. Wait a minute and try again.";
  if (reason === "timeout" || code === "timeout") return "Transcription took too long. Try again, or try a shorter recording.";
  return "We couldn’t transcribe this audio. Try again in a minute.";
}

/** XHR rather than fetch: its upload events tell us honestly when uploading ends and transcribing starts. */
function sendAudio(form: FormData, onUploaded: () => void): Promise<Outcome> {
  return new Promise((resolve) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/transcribe");
    xhr.upload.onload = onUploaded;
    xhr.onload = () => {
      let body: { error?: { code?: string; reason?: string | null } } | null = null;
      try {
        body = JSON.parse(xhr.responseText); // leading heartbeat whitespace is valid JSON
      } catch {
        body = null;
      }
      if (xhr.status === 200 && body && !body.error) return resolve({ ok: true, result: body as TranscribeResult });
      resolve({ ok: false, code: body?.error?.code ?? `http_${xhr.status}`, reason: body?.error?.reason ?? null });
    };
    xhr.onerror = () => resolve({ ok: false, code: "network", reason: null });
    xhr.send(form);
  });
}

function durationOf(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const probe = new Audio();
    const done = (seconds: number | null) => {
      URL.revokeObjectURL(url);
      resolve(seconds !== null && Number.isFinite(seconds) ? seconds : null);
    };
    probe.preload = "metadata";
    probe.onloadedmetadata = () => done(probe.duration);
    probe.onerror = () => done(null);
    probe.src = url;
  });
}

const inkButton = "btn bg-ink text-paper hover:bg-ink-soft disabled:cursor-not-allowed disabled:opacity-50";
const plainButton = "btn btn-secondary disabled:cursor-not-allowed disabled:opacity-50";

function MicProblem({ phase }: { phase: RecorderState["phase"] }) {
  const copy: Partial<Record<RecorderState["phase"], [string, string]>> = {
    denied: [
      "Your browser blocked the microphone.",
      "Click the icon to the left of the address bar, allow the microphone for this site, then press Start recording again.",
    ],
    "no-mic": ["We couldn’t find a microphone.", "Plug one in or check your system sound settings, then try again."],
    unsupported: ["This browser can’t record audio.", "Use a recent Chrome, Edge, Firefox or Safari, or upload a recording instead."],
    failed: ["The microphone didn’t start.", "Try again, or upload a recording instead."],
  };
  const text = copy[phase];
  if (!text) return null;
  return (
    <p role="alert" className="m-0 text-[15px] leading-normal text-ink-soft">
      <strong className="text-danger">{text[0]}</strong> {text[1]}
    </p>
  );
}

export function AudioInput({
  ideaId,
  mode,
  limits,
  consent,
  onConsentChange,
  onTranscript,
}: {
  ideaId: string;
  mode: "record" | "audio";
  limits: AudioLimits;
  consent: boolean;
  onConsentChange: (value: boolean) => void;
  onTranscript: (transcript: string) => void;
}) {
  const maxSeconds = limits.maxMinutes * 60;
  const recorder = useRecorder(maxSeconds);
  const [people, setPeople] = useState(2);
  const [chosen, setChosen] = useState<{ file: File; seconds: number | null } | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [flow, setFlow] = useState<Flow>({ step: "capture" });
  const rec = recorder.state;

  async function transcribe(pending: Pending) {
    setFlow({ step: "sending", pending, phase: "uploading" });
    const form = new FormData();
    form.set("idea_id", ideaId);
    form.set("consent", consent ? "true" : "false");
    form.set("num_speakers", String(people));
    form.set("file", pending.blob, pending.name);
    const outcome = await sendAudio(form, () =>
      setFlow((current) => (current.step === "sending" ? { ...current, phase: "transcribing" } : current)),
    );
    if (outcome.ok) setFlow({ step: "review", result: outcome.result, founderId: outcome.result.suggested_founder_id });
    else setFlow({ step: "failed", message: failureCopy(outcome.code, outcome.reason, limits.maxMb) });
  }

  async function onFile(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setChosen(null);
    if (!audioExtension(file.name, file.type)) return setFileError(`We can only read ${FORMATS} files.`);
    if (file.size > limits.maxMb * 1024 * 1024) {
      return setFileError(`This file is ${fileSize(file.size)}; the limit is ${limits.maxMb} MB. Export it as .m4a or .mp3 to make it smaller.`);
    }
    setFileError(null);
    setChosen({ file, seconds: await durationOf(file) });
  }

  if (flow.step === "sending") {
    const { pending, phase } = flow;
    return (
      <div aria-live="polite" className="flex flex-col gap-3 rounded-[18px] border-[2.5px] border-ink bg-paper p-5">
        <strong className="font-serif text-[24px] font-medium">
          {phase === "uploading" ? "Uploading your audio." : "Transcribing your interview."}
        </strong>
        <span className="text-[15px] leading-normal text-ink-soft">
          {phase === "uploading" ? `Uploading ${fileSize(pending.blob.size)}…` : transcribingCopy(pending.seconds)}
        </span>
        <span aria-hidden="true" className="h-2 w-full rounded-[7px] bg-line motion-safe:animate-pulse-soft" />
      </div>
    );
  }

  if (flow.step === "failed") {
    return (
      <div role="alert" className="flex flex-col gap-3 rounded-[18px] border-[2.5px] border-danger bg-white p-5">
        <strong className="text-[17px] text-danger">Transcription failed.</strong>
        <span className="text-[15px] leading-normal text-ink-soft">{flow.message}</span>
        <div>
          <button type="button" className={plainButton} onClick={() => setFlow({ step: "capture" })}>
            Back to my audio
          </button>
        </div>
      </div>
    );
  }

  if (flow.step === "review") {
    const { result, founderId } = flow;
    return (
      <div className="flex flex-col gap-4">
        <fieldset className="m-0 flex flex-col gap-3 border-0 p-0">
          <legend className="mb-3 p-0">
            <strong className="block text-[17px]">Which voice is you?</strong>
            <span className="block text-sm leading-normal text-muted">
              We guessed. Check it. Every other voice becomes the customer.
            </span>
          </legend>
          {result.speakers.map((speaker, index) => {
            const mine = speaker.id === founderId;
            return (
              <label
                key={speaker.id}
                className={`flex cursor-pointer flex-col gap-2.5 rounded-[14px] border-[2.5px] border-ink p-4 has-[:focus-visible]:outline-3 has-[:focus-visible]:outline-brand ${
                  mine ? "bg-paper" : "bg-white"
                }`}
              >
                <span className="flex flex-wrap items-center justify-between gap-2">
                  <span className="flex items-center gap-2.5">
                    <input
                      type="radio"
                      name="founder-voice"
                      value={speaker.id}
                      checked={mine}
                      onChange={() => setFlow({ ...flow, founderId: speaker.id })}
                      aria-label={`Voice ${index + 1} is me`}
                      className="size-5 accent-ink"
                    />
                    <strong className="text-[15px]">Voice {index + 1}</strong>
                    <span className={`tag ${mine ? "tag-dark" : ""}`}>{mine ? "This is me" : "Customer"}</span>
                  </span>
                  <span className="text-sm text-muted">
                    {clock(speaker.seconds)} talking · {speaker.turns === 1 ? "1 turn" : `${speaker.turns} turns`}
                  </span>
                </span>
                <span className="flex flex-col gap-1 border-l-[2.5px] border-line pl-3">
                  {speaker.sample.map((line, i) => (
                    <q key={i} className="text-[15px] leading-snug text-ink-soft">
                      {line}
                    </q>
                  ))}
                </span>
              </label>
            );
          })}
        </fieldset>
        {result.speakers.length === 1 && (
          <p role="status" className="m-0 rounded-[14px] border-[2.5px] border-ink bg-white p-4 text-[15px] leading-normal text-ink-soft">
            <strong className="text-ink">We only heard one voice.</strong> The person you interviewed may not be audible on this
            recording. You can still send it, and the read-out will say what evidence is missing.
          </p>
        )}
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            className={inkButton}
            onClick={() => {
              onTranscript(buildTranscript(result.turns, founderId));
              setFlow({ step: "capture" });
            }}
          >
            Use this transcript
          </button>
          <button type="button" className={plainButton} onClick={() => setFlow({ step: "capture" })}>
            Back to my audio
          </button>
        </div>
      </div>
    );
  }

  const peopleSelect = (
    <label className="flex flex-wrap items-center gap-2.5 text-[15px] font-bold">
      People in the conversation
      <select
        value={people}
        onChange={(e) => setPeople(Number(e.target.value))}
        className="min-h-11 rounded-xl border-[2.5px] border-ink bg-white px-3 font-sans text-[15px] text-ink"
      >
        {PEOPLE.map((n) => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </select>
    </label>
  );

  return (
    <div className="flex flex-col gap-4">
      <label className="flex cursor-pointer items-start gap-3 rounded-[14px] border-[2.5px] border-ink bg-paper p-4 text-base leading-snug">
        <input
          type="checkbox"
          checked={consent}
          onChange={(e) => onConsentChange(e.target.checked)}
          className="mt-0.5 size-6 shrink-0 accent-brand"
        />
        <span className="flex flex-col gap-1">
          <span>The person I’m interviewing knows this conversation is being recorded and agreed to it.</span>
          <span className="text-sm text-muted">We send the audio to our transcription provider (ElevenLabs) and don’t keep it.</span>
        </span>
      </label>

      {mode === "record" ? (
        <div className="flex flex-col gap-3.5 rounded-[14px] border-[2.5px] border-ink bg-white p-4">
          {rec.phase === "recording" ? (
            <>
              <div className="flex flex-wrap items-center gap-3" aria-live="polite">
                <span aria-hidden="true" className="size-3 rounded-full bg-ink motion-safe:animate-pulse-soft" />
                <strong className="text-[15px]">Recording</strong>
                <span className="font-mono text-[15px]">
                  {clock(recorder.elapsed)} / {clock(maxSeconds)}
                </span>
                <span
                  role="meter"
                  aria-label="Microphone level"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={Math.round(recorder.level * 100)}
                  className="h-2 w-32 overflow-hidden rounded-[7px] bg-line"
                >
                  <span className="block h-full bg-ink" style={{ width: `${Math.round(recorder.level * 100)}%` }} />
                </span>
              </div>
              {recorder.elapsed >= maxSeconds - WARN_BEFORE_END_S && (
                <p role="status" className="m-0 text-[15px] text-ink-soft">
                  <strong className="text-ink">{Math.max(1, Math.ceil((maxSeconds - recorder.elapsed) / 60))} min left.</strong>{" "}
                  Recording stops by itself at {clock(maxSeconds)}.
                </p>
              )}
              <div>
                <button type="button" className={inkButton} onClick={recorder.stop}>
                  Stop
                </button>
              </div>
            </>
          ) : rec.phase === "recorded" ? (
            <>
              <audio controls src={rec.url} className="w-full">
                <track kind="captions" />
              </audio>
              <span className="text-sm text-muted">
                {clock(rec.seconds)} · {fileSize(rec.blob.size)}
                {rec.hitLimit && ` · Stopped at the ${limits.maxMinutes}-minute limit.`}
              </span>
              {peopleSelect}
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  className={inkButton}
                  disabled={!consent}
                  onClick={() =>
                    transcribe({ blob: rec.blob, name: `recording${extensionFor(rec.blob.type)}`, seconds: rec.seconds })
                  }
                >
                  Use this recording
                </button>
                <button type="button" className={plainButton} onClick={recorder.reset}>
                  Record again
                </button>
              </div>
            </>
          ) : (
            <>
              <span className="text-sm leading-normal text-muted">
                Recording uses this device’s microphone, so it suits in-person interviews. For Zoom or Meet, upload the call
                recording instead.
              </span>
              <div>
                <button type="button" className={inkButton} disabled={!consent || rec.phase === "asking"} onClick={recorder.start}>
                  {rec.phase === "asking" ? "Waiting for the microphone…" : "Start recording"}
                </button>
              </div>
              {rec.phase === "asking" && <span className="text-sm text-muted">Allow the microphone when your browser asks.</span>}
              <MicProblem phase={rec.phase} />
            </>
          )}
          {!consent && rec.phase !== "recording" && <span className="text-sm text-muted">Tick the box above first.</span>}
        </div>
      ) : (
        <div className="flex flex-col gap-3.5">
          {chosen ? (
            <div className="flex flex-col gap-3.5 rounded-[14px] border-[2.5px] border-ink bg-white p-4">
              <span className="text-[15px]">
                <strong className="break-all">{chosen.file.name}</strong>
                <span className="text-muted">
                  {" "}
                  · {fileSize(chosen.file.size)}
                  {chosen.seconds !== null && ` · ${clock(chosen.seconds)}`}
                </span>
              </span>
              {peopleSelect}
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  className={inkButton}
                  disabled={!consent}
                  onClick={() => transcribe({ blob: chosen.file, name: chosen.file.name, seconds: chosen.seconds })}
                >
                  Transcribe this file
                </button>
                <button type="button" className={plainButton} onClick={() => setChosen(null)}>
                  Choose another file
                </button>
              </div>
            </div>
          ) : (
            <label
              className={`relative flex flex-col items-center gap-2 rounded-[14px] border-[2.5px] border-ink bg-paper px-5 py-8 text-center ${
                consent ? "cursor-pointer" : "cursor-not-allowed opacity-60"
              }`}
            >
              <strong className="text-[17px]">Choose an audio file</strong>
              <span className="text-sm text-muted">
                {FORMATS}, up to {limits.maxMb} MB. M4A and MP3 upload fastest.
              </span>
              <input
                type="file"
                aria-label="Choose an audio file"
                accept=".mp3,.m4a,.wav,.webm,.ogg,.mp4,audio/*,video/mp4"
                disabled={!consent}
                onChange={onFile}
                className="absolute inset-0 cursor-pointer opacity-0 disabled:cursor-not-allowed"
              />
            </label>
          )}
          {fileError && (
            <p role="alert" className="m-0 text-[15px] leading-normal text-ink-soft">
              <strong className="text-danger">Can’t use this file.</strong> {fileError}
            </p>
          )}
          {!consent && <span className="text-sm text-muted">Tick the box above first.</span>}
        </div>
      )}
    </div>
  );
}
