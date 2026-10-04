import { randomUUID } from "node:crypto";
import { describe, expect, it } from "vitest";

import { decodeSession, encodeSession } from "@/lib/session";

describe("session cookie", () => {
  it("round-trips a signed founder id", () => {
    const id = randomUUID();
    expect(decodeSession(encodeSession(id))).toBe(id);
  });

  it("rejects a tampered founder id", () => {
    const [, signature] = encodeSession(randomUUID()).split(".");
    expect(decodeSession(`${randomUUID()}.${signature}`)).toBeNull();
  });

  it("rejects garbage and missing values", () => {
    expect(decodeSession(undefined)).toBeNull();
    expect(decodeSession("not-a-session")).toBeNull();
    expect(decodeSession("abc.def")).toBeNull();
  });
});
