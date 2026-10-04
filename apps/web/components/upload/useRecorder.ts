"use client";

// In-browser recording with MediaRecorder. The audio stays in this tab as a Blob until the founder chooses
// "Use this recording"; we never keep it anywhere.
import { useCallback, useEffect, useRef, useState } from "react";

export type RecorderState =
  | { phase: "idle" }
  | { phase: "asking" }
  | { phase: "recording" }
  | { phase: "recorded"; blob: Blob; url: string; seconds: number; hitLimit: boolean }
  | { phase: "denied" }
  | { phase: "no-mic" }
  | { phase: "unsupported" }
  | { phase: "failed" };

// Opus in WebM where supported (Chrome, Firefox, Edge), else MP4/AAC (Safari).
const MIME_TYPES = ["audio/webm;codecs=opus", "audio/mp4"] as const;
// Speech is clear at 64 kbit/s, and an hour stays near 29 MB.
const BITS_PER_SECOND = 64_000;
const TICK_MS = 250;
const LEVEL_EVERY_MS = 100;

export function pickMimeType(isSupported: (type: string) => boolean): string | null {
  return MIME_TYPES.find((type) => isSupported(type)) ?? null;
}

export function extensionFor(mimeType: string): ".webm" | ".m4a" {
  return mimeType.startsWith("audio/mp4") ? ".m4a" : ".webm";
}

interface Live {
  stream?: MediaStream;
  recorder?: MediaRecorder;
  context?: AudioContext;
  frame?: number;
  timer?: ReturnType<typeof setInterval>;
  url?: string;
  chunks: Blob[];
}

export function useRecorder(maxSeconds: number) {
  const [state, setState] = useState<RecorderState>({ phase: "idle" });
  const [elapsed, setElapsed] = useState(0);
  const [level, setLevel] = useState(0);
  const live = useRef<Live>({ chunks: [] });

  /** Stops every track, so the browser's microphone indicator turns off. */
  const releaseMic = useCallback(() => {
    const current = live.current;
    current.stream?.getTracks().forEach((track) => track.stop());
    current.stream = undefined;
    if (current.frame !== undefined) cancelAnimationFrame(current.frame);
    if (current.timer !== undefined) clearInterval(current.timer);
    current.frame = current.timer = undefined;
    current.context?.close().catch(() => undefined);
    current.context = undefined;
  }, []);

  const forgetRecording = useCallback(() => {
    if (live.current.url) URL.revokeObjectURL(live.current.url);
    live.current.url = undefined;
  }, []);

  const start = useCallback(async () => {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") return setState({ phase: "unsupported" });
    const mimeType = pickMimeType((type) => MediaRecorder.isTypeSupported(type));
    if (!mimeType) return setState({ phase: "unsupported" });
    forgetRecording();
    setElapsed(0);
    setLevel(0);
    setState({ phase: "asking" });

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } });
    } catch (error) {
      const name = error instanceof DOMException ? error.name : "";
      if (name === "NotAllowedError" || name === "SecurityError") return setState({ phase: "denied" });
      if (name === "NotFoundError" || name === "OverconstrainedError") return setState({ phase: "no-mic" });
      return setState({ phase: "failed" });
    }

    const current = live.current;
    current.stream = stream;
    current.chunks = [];
    const recorder = new MediaRecorder(stream, { mimeType, audioBitsPerSecond: BITS_PER_SECOND });
    current.recorder = recorder;
    const startedAt = performance.now();
    let hitLimit = false;

    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) current.chunks.push(event.data);
    };
    recorder.onstop = () => {
      const seconds = (performance.now() - startedAt) / 1000;
      const blob = new Blob(current.chunks, { type: mimeType.split(";")[0] });
      current.chunks = [];
      releaseMic();
      current.url = URL.createObjectURL(blob);
      setLevel(0);
      setState({ phase: "recorded", blob, url: current.url, seconds, hitLimit });
    };

    // Level meter: loudness of the last few milliseconds, refreshed about 10 times a second.
    try {
      const context = new AudioContext();
      const analyser = context.createAnalyser();
      analyser.fftSize = 512;
      context.createMediaStreamSource(stream).connect(analyser);
      current.context = context;
      const samples = new Uint8Array(analyser.fftSize);
      let lastPaint = 0;
      const paint = (now: number) => {
        if (now - lastPaint >= LEVEL_EVERY_MS) {
          analyser.getByteTimeDomainData(samples);
          let sum = 0;
          for (const sample of samples) sum += ((sample - 128) / 128) ** 2;
          setLevel(Math.min(1, Math.sqrt(sum / samples.length) * 4));
          lastPaint = now;
        }
        current.frame = requestAnimationFrame(paint);
      };
      current.frame = requestAnimationFrame(paint);
    } catch {
      // No meter is fine; recording still works.
    }

    current.timer = setInterval(() => {
      const seconds = (performance.now() - startedAt) / 1000;
      setElapsed(seconds);
      if (seconds >= maxSeconds && recorder.state === "recording") {
        hitLimit = true;
        recorder.stop();
      }
    }, TICK_MS);
    recorder.start(1000);
    setState({ phase: "recording" });
  }, [forgetRecording, maxSeconds, releaseMic]);

  const stop = useCallback(() => {
    if (live.current.recorder?.state === "recording") live.current.recorder.stop();
  }, []);

  const reset = useCallback(() => {
    forgetRecording();
    setElapsed(0);
    setState({ phase: "idle" });
  }, [forgetRecording]);

  // Leaving the page (or this mode) must never leave the microphone on.
  useEffect(() => {
    const current = live.current;
    return () => {
      if (current.recorder && current.recorder.state !== "inactive") {
        current.recorder.onstop = null;
        current.recorder.stop();
      }
      releaseMic();
      if (current.url) URL.revokeObjectURL(current.url);
    };
  }, [releaseMic]);

  // Leaving while recording asks first: a reload or tab close, or a link inside the app.
  const recording = state.phase === "recording";
  useEffect(() => {
    if (!recording) return;
    const onUnload = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = "";
    };
    const onLinkClick = (event: MouseEvent) => {
      const link = (event.target as Element | null)?.closest?.("a[href]");
      if (!link || link.getAttribute("target") === "_blank") return;
      if (!window.confirm("You are still recording. Leave this page and lose the recording?")) event.preventDefault();
    };
    window.addEventListener("beforeunload", onUnload);
    document.addEventListener("click", onLinkClick, true);
    return () => {
      window.removeEventListener("beforeunload", onUnload);
      document.removeEventListener("click", onLinkClick, true);
    };
  }, [recording]);

  return { state, elapsed, level, start, stop, reset };
}
