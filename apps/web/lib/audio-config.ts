// Audio input switches. Read on the server only; pages pass them to the client as props.
// With AUDIO_INPUT_ENABLED unset (or anything but "true") the app behaves exactly as before audio existed:
// no audio modes in the upload form and /api/transcribe answers 404.

export const AUDIO_EXTENSIONS = [".mp3", ".m4a", ".wav", ".webm", ".ogg", ".mp4"] as const;
export type AudioExtension = (typeof AUDIO_EXTENSIONS)[number];

const EXTENSION_BY_TYPE: Record<string, AudioExtension> = {
  "audio/mpeg": ".mp3",
  "audio/mp3": ".mp3",
  "audio/mp4": ".m4a",
  "audio/x-m4a": ".m4a",
  "audio/aac": ".m4a",
  "audio/wav": ".wav",
  "audio/x-wav": ".wav",
  "audio/wave": ".wav",
  "audio/webm": ".webm",
  "audio/ogg": ".ogg",
  "video/mp4": ".mp4",
  "video/webm": ".webm",
};

export interface AudioConfig {
  enabled: boolean;
  maxMb: number;
  maxMinutes: number;
}

function positiveInt(raw: string | undefined, fallback: number): number {
  const value = Number(raw);
  return Number.isInteger(value) && value > 0 ? value : fallback;
}

export function audioConfig(): AudioConfig {
  return {
    enabled: process.env.AUDIO_INPUT_ENABLED === "true",
    maxMb: positiveInt(process.env.AUDIO_MAX_MB, 100),
    maxMinutes: positiveInt(process.env.AUDIO_MAX_MINUTES, 60),
  };
}

/** The file's extension when we accept it, from its name first and then its MIME type; otherwise null. */
export function audioExtension(name: string, type: string): AudioExtension | null {
  const fromName = name.toLowerCase().match(/\.[a-z0-9]+$/)?.[0];
  if (fromName && (AUDIO_EXTENSIONS as readonly string[]).includes(fromName)) return fromName as AudioExtension;
  return EXTENSION_BY_TYPE[type.split(";")[0].trim().toLowerCase()] ?? null;
}
