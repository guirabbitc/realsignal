// Drizzle schema: the source of truth for Postgres (SPEC §8). Only apps/web touches the database.
import {
  boolean, integer, jsonb, pgEnum, pgTable, real, text, timestamp, uniqueIndex, index, uuid,
} from "drizzle-orm/pg-core";

export const interviewKind = pgEnum("interview_kind", ["interview", "demo"]);
export const inputSource = pgEnum("input_source", ["text", "audio", "video"]);
export const interviewStatus = pgEnum("interview_status", ["processing", "done", "failed"]);
export const category = pgEnum("category", ["commitment", "past_pain", "hypothetical", "compliment", "neutral"]);
export const verdict = pgEnum("verdict", ["keep_going", "narrow_down", "new_angle", "pivot", "need_more_evidence"]);

export const founders = pgTable("founders", {
  id: uuid("id").primaryKey().defaultRandom(),
  email: text("email").unique(),
  name: text("name"),
  asiAddress: text("asi_address").unique(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

export const ideas = pgTable("ideas", {
  id: uuid("id").primaryKey().defaultRandom(),
  founderId: uuid("founder_id").notNull().references(() => founders.id, { onDelete: "cascade" }),
  oneLiner: text("one_liner").notNull(),
  targetCustomer: text("target_customer"),
  isCurrent: boolean("is_current").notNull().default(true),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
}, (t) => [index("ideas_founder_id_idx").on(t.founderId)]);

export const interviews = pgTable("interviews", {
  id: uuid("id").primaryKey().defaultRandom(),
  ideaId: uuid("idea_id").notNull().references(() => ideas.id, { onDelete: "cascade" }),
  kind: interviewKind("kind").notNull(),
  intervieweeLabel: text("interviewee_label"),
  source: inputSource("source").notNull().default("text"),
  transcript: text("transcript").notNull(),
  status: interviewStatus("status").notNull().default("processing"),
  error: text("error"),
  founderTalkRatio: real("founder_talk_ratio"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
}, (t) => [index("interviews_idea_id_created_at_idx").on(t.ideaId, t.createdAt)]);

export const statements = pgTable("statements", {
  id: uuid("id").primaryKey().defaultRandom(),
  interviewId: uuid("interview_id").notNull().references(() => interviews.id, { onDelete: "cascade" }),
  position: integer("position").notNull(),
  quote: text("quote").notNull(),
  founderQuestion: text("founder_question"),
  category: category("category").notNull(),
  categoryProbs: jsonb("category_probs").$type<Record<string, number>>().notNull(),
  pReal: real("p_real").notNull(),
  confidence: real("confidence").notNull(),
}, (t) => [uniqueIndex("statements_interview_position_uq").on(t.interviewId, t.position)]);

export const analyses = pgTable("analyses", {
  id: uuid("id").primaryKey().defaultRandom(),
  interviewId: uuid("interview_id").notNull().unique().references(() => interviews.id, { onDelete: "cascade" }),
  score: integer("score"),
  verdict: verdict("verdict").notNull(),
  verdictConfidence: real("verdict_confidence"),
  pitchedEarly: real("pitched_early"),
  leadingQuestions: real("leading_questions"),
  summary: text("summary").notNull(),
  reasons: jsonb("reasons").$type<string[]>().notNull(),
  nextQuestions: jsonb("next_questions").$type<string[]>().notNull(),
  missingEvidence: text("missing_evidence"),
  modelVersions: jsonb("model_versions").$type<Record<string, unknown>>().notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});

// Created now, used after the MVP (SPEC §8).
export const ideaReports = pgTable("idea_reports", {
  id: uuid("id").primaryKey().defaultRandom(),
  ideaId: uuid("idea_id").notNull().references(() => ideas.id, { onDelete: "cascade" }),
  interviewCount: integer("interview_count").notNull(),
  aggregateScore: integer("aggregate_score"),
  verdict: verdict("verdict").notNull(),
  reportMd: text("report_md").notNull(),
  paid: boolean("paid").notNull().default(false),
  paymentRef: text("payment_ref"),
  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
});
