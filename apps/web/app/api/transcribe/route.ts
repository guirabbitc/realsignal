// Audio → voices and turns, so the founder can say which voice is theirs. Stores nothing: the audio goes to the
// analyzer (which sends it to ElevenLabs) and the transcript only comes back to this browser.
// A route handler, not a server action: server actions cap bodies at 1 MB. If a proxy (ex-middleware) is ever
// added, Next.js buffers bodies only up to proxyClientMaxBodySize (10 MB by default) and audio uploads break.
import { z } from "zod";

import { AnalyzerCallError, transcribe } from "@/lib/analyzer-client";
import { AUDIO_EXTENSIONS, audioConfig, audioExtension } from "@/lib/audio-config";
import { founderOwnsIdea } from "@/lib/db/queries";
import { invalid, json, notFound } from "@/lib/http";
import { getFounderId } from "@/lib/session";

export const runtime = "nodejs";
export const maxDuration = 300;

// Railway closes a request after 5 minutes without a byte, and transcription can take minutes.
const HEARTBEAT_MS = 15_000;
const MULTIPART_OVERHEAD_BYTES = 64 * 1024;

const fieldsSchema = z.object({
  idea_id: z.uuid(),
  consent: z.string().optional(),
  num_speakers: z.coerce.number().int().min(1).max(4).default(2),
});

function tooLarge(maxMb: number): Response {
  return json({ error: { code: "audio_too_large", message: `The audio is larger than ${maxMb} MB.` } }, 413);
}

export async function POST(request: Request) {
  const config = audioConfig();
  if (!config.enabled) return notFound();
  const founderId = await getFounderId();
  if (!founderId) return notFound();
  const maxBytes = config.maxMb * 1024 * 1024;
  // An obviously oversized body is refused before it is buffered.
  if (Number(request.headers.get("content-length") ?? 0) > maxBytes + MULTIPART_OVERHEAD_BYTES) return tooLarge(config.maxMb);

  let form: FormData;
  try {
    form = await request.formData();
  } catch {
    return invalid("Send multipart form data with idea_id, consent, num_speakers and file.");
  }
  const fields = fieldsSchema.safeParse({
    idea_id: form.get("idea_id"),
    consent: form.get("consent") ?? undefined,
    num_speakers: form.get("num_speakers") ?? undefined,
  });
  if (!fields.success) return invalid("Send idea_id, consent, num_speakers (1 to 4) and file.");
  const { idea_id: ideaId, consent, num_speakers: numSpeakers } = fields.data;
  if (!(await founderOwnsIdea(founderId, ideaId))) return notFound();
  if (consent !== "true") {
    return json({ error: { code: "consent_required", message: "Confirm the person you interviewed knows it was recorded." } }, 400);
  }

  const file = form.get("file");
  if (!(file instanceof File)) return invalid("Send the audio in a field named file.");
  if (file.size > maxBytes) return tooLarge(config.maxMb);
  if (file.size === 0) return json({ error: { code: "empty_audio", message: "The audio file is empty." } }, 422);
  const extension = audioExtension(file.name, file.type);
  if (!extension) return invalid(`Send one of: ${AUDIO_EXTENSIONS.join(", ")}.`);

  const encoder = new TextEncoder();
  let beat: ReturnType<typeof setInterval> | undefined;
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      const send = (text: string) => {
        try {
          controller.enqueue(encoder.encode(text));
        } catch {
          // The browser went away; nothing left to tell it.
        }
      };
      // Leading whitespace is valid JSON, so these bytes keep the connection alive without changing the body.
      send(" ");
      beat = setInterval(() => send(" "), HEARTBEAT_MS);
      const started = Date.now();
      transcribe(file, extension, numSpeakers)
        .then((result) => {
          send(JSON.stringify(result));
          console.info(
            `transcribe done idea=${ideaId} ms=${Date.now() - started} bytes=${file.size} voices=${result.speakers.length} turns=${result.turns.length}`,
          );
        })
        .catch((error: unknown) => {
          const code = error instanceof AnalyzerCallError ? error.code : "internal_error";
          const reason = error instanceof AnalyzerCallError ? error.reason : null;
          // Outcome in-band: the 200 status went out with the first heartbeat byte.
          send(JSON.stringify({ error: { code, message: "Transcription failed.", reason } }));
          console.warn(`transcribe failed idea=${ideaId} ms=${Date.now() - started} bytes=${file.size} code=${code} reason=${reason}`);
        })
        .finally(() => {
          clearInterval(beat);
          try {
            controller.close();
          } catch {
            // Already closed by a cancelled reader.
          }
        });
    },
    cancel() {
      clearInterval(beat);
    },
  });
  return new Response(body, {
    status: 200,
    // no-transform keeps response compression from holding the heartbeat bytes back.
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store, no-transform", "x-accel-buffering": "no" },
  });
}
