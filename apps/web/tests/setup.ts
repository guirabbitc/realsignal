import "dotenv/config";

process.env.SESSION_SECRET ??= "test-session-secret-that-is-at-least-32-chars";
