// The ONLY code that reads or writes the session cookie (SPEC §7, MISSION invariant 1).
// founder_id comes from here and nowhere else: never from a body, query string or path.
import { createHmac, timingSafeEqual } from "node:crypto";
import { cookies } from "next/headers";

import { createFounder, founderExists } from "./db/queries";

export const SESSION_COOKIE = "vai_sid";
const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

function secret(): string {
  const value = process.env.SESSION_SECRET;
  if (!value || value.length < 32) throw new Error("SESSION_SECRET must be set (32+ characters)");
  return value;
}

function sign(founderId: string): string {
  return createHmac("sha256", secret()).update(founderId).digest("base64url");
}

export function encodeSession(founderId: string): string {
  return `${founderId}.${sign(founderId)}`;
}

/** Returns the founder id if the cookie value is well-formed and correctly signed; otherwise null. */
export function decodeSession(value: string | undefined): string | null {
  if (!value) return null;
  const dot = value.indexOf(".");
  if (dot < 0) return null;
  const founderId = value.slice(0, dot);
  const given = Buffer.from(value.slice(dot + 1));
  const expected = Buffer.from(sign(founderId));
  if (!UUID.test(founderId) || given.length !== expected.length || !timingSafeEqual(given, expected)) return null;
  return founderId;
}

export async function getFounderId(): Promise<string | null> {
  return decodeSession((await cookies()).get(SESSION_COOKIE)?.value);
}

/** Route handlers and server actions only (cookies cannot be set during RSC render). */
export async function getOrCreateFounderId(): Promise<string> {
  const existing = await getFounderId();
  if (existing && (await founderExists(existing))) return existing;
  const founderId = await createFounder();
  (await cookies()).set({
    name: SESSION_COOKIE,
    value: encodeSession(founderId),
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: ONE_YEAR_SECONDS,
  });
  return founderId;
}
