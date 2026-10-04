import {
  boolean,
  integer,
  jsonb,
  pgEnum,
  pgTable,
  real,
  text,
  timestamp,
  uuid,
} from "drizzle-orm/pg-core";
import type { AnalyzeResponse } from "../contracts/analyze";
import { LABELS, VERDICTS } from "../contracts/values";

export const interviewStatus = pgEnum("interview_status", ["processing", "done", "failed"]);
export const interviewSource = pgEnum("interview_source", ["transcript", "audio"]);
export const signalLabel = pgEnum("signal_label", LABELS);
export const verdictValue = pgEnum("verdict", VERDICTS);

const id = uuid("id").primaryKey().defaultRandom();
const createdAt = timestamp("created_at", { withTimezone: true }).notNull().defaultNow();

export const founders = pgTable("founders", {
  id,
  email: text("email").notNull().unique(),
  name: text("name").notNull(),
  createdAt,
});

export const ideas = pgTable("ideas", {
  id,
  founderId: uuid("founder_id").notNull().references(() => founders.id, { onDelete: "cascade" }),
  title: text("title").notNull(),
  description: text("description").notNull(),
  createdAt,
});

export const interviews = pgTable("interviews", {
  id,
  ideaId: uuid("idea_id").notNull().references(() => ideas.id, { onDelete: "cascade" }),
  title: text("title").notNull(),
  source: interviewSource("source").notNull(),
  // Null for audio until the analyzer returns the transcript. Audio itself is not stored.
  transcript: text("transcript"),
  status: interviewStatus("status").notNull().default("processing"),
  error: text("error"),
  createdAt,
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

// One row per sentence. Interviewer sentences are not judged: label and confidence are null.
export const signals = pgTable("signals", {
  id,
  interviewId: uuid("interview_id").notNull().references(() => interviews.id, { onDelete: "cascade" }),
  order: integer("order").notNull(),
  speaker: text("speaker").notNull(),
  text: text("text").notNull(),
  isInterviewee: boolean("is_interviewee").notNull(),
  label: signalLabel("label"),
  confidence: real("confidence"),
  createdAt,
});

export const analyses = pgTable("analyses", {
  id,
  interviewId: uuid("interview_id").notNull().unique().references(() => interviews.id, { onDelete: "cascade" }),
  score: real("score").notNull(),
  verdict: verdictValue("verdict").notNull(),
  summary: text("summary").notNull(),
  nextSteps: jsonb("next_steps").$type<string[]>().notNull(),
  raw: jsonb("raw").$type<AnalyzeResponse>().notNull(),
  createdAt,
});
