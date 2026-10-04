import { z } from "zod";

export const uuidSchema = z.uuid();

export function json(body: unknown, status = 200): Response {
  return Response.json(body, { status });
}

export function notFound(): Response {
  return json({ error: { code: "not_found", message: "Not found." } }, 404);
}

export function invalid(message: string): Response {
  return json({ error: { code: "invalid_request", message } }, 422);
}

export async function readJson(request: Request): Promise<unknown> {
  try {
    return await request.json();
  } catch {
    return undefined;
  }
}
