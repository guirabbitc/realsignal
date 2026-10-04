CREATE TYPE "public"."category" AS ENUM('commitment', 'past_pain', 'hypothetical', 'compliment', 'neutral');--> statement-breakpoint
CREATE TYPE "public"."input_source" AS ENUM('text', 'audio', 'video');--> statement-breakpoint
CREATE TYPE "public"."interview_kind" AS ENUM('interview', 'demo');--> statement-breakpoint
CREATE TYPE "public"."interview_status" AS ENUM('processing', 'done', 'failed');--> statement-breakpoint
CREATE TYPE "public"."verdict" AS ENUM('keep_going', 'narrow_down', 'new_angle', 'pivot', 'need_more_evidence');--> statement-breakpoint
CREATE TABLE "analyses" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"interview_id" uuid NOT NULL,
	"score" integer,
	"verdict" "verdict" NOT NULL,
	"verdict_confidence" real,
	"pitched_early" real,
	"leading_questions" real,
	"summary" text NOT NULL,
	"reasons" jsonb NOT NULL,
	"next_questions" jsonb NOT NULL,
	"missing_evidence" text,
	"model_versions" jsonb NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "analyses_interview_id_unique" UNIQUE("interview_id")
);
--> statement-breakpoint
CREATE TABLE "founders" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"email" text,
	"name" text,
	"asi_address" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "founders_email_unique" UNIQUE("email"),
	CONSTRAINT "founders_asi_address_unique" UNIQUE("asi_address")
);
--> statement-breakpoint
CREATE TABLE "idea_reports" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"idea_id" uuid NOT NULL,
	"interview_count" integer NOT NULL,
	"aggregate_score" integer,
	"verdict" "verdict" NOT NULL,
	"report_md" text NOT NULL,
	"paid" boolean DEFAULT false NOT NULL,
	"payment_ref" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "ideas" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"founder_id" uuid NOT NULL,
	"one_liner" text NOT NULL,
	"target_customer" text,
	"is_current" boolean DEFAULT true NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "interviews" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"idea_id" uuid NOT NULL,
	"kind" "interview_kind" NOT NULL,
	"interviewee_label" text,
	"source" "input_source" DEFAULT 'text' NOT NULL,
	"transcript" text NOT NULL,
	"status" "interview_status" DEFAULT 'processing' NOT NULL,
	"error" text,
	"founder_talk_ratio" real,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "statements" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"interview_id" uuid NOT NULL,
	"position" integer NOT NULL,
	"quote" text NOT NULL,
	"founder_question" text,
	"category" "category" NOT NULL,
	"category_probs" jsonb NOT NULL,
	"p_real" real NOT NULL,
	"confidence" real NOT NULL
);
--> statement-breakpoint
ALTER TABLE "analyses" ADD CONSTRAINT "analyses_interview_id_interviews_id_fk" FOREIGN KEY ("interview_id") REFERENCES "public"."interviews"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "idea_reports" ADD CONSTRAINT "idea_reports_idea_id_ideas_id_fk" FOREIGN KEY ("idea_id") REFERENCES "public"."ideas"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "ideas" ADD CONSTRAINT "ideas_founder_id_founders_id_fk" FOREIGN KEY ("founder_id") REFERENCES "public"."founders"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "interviews" ADD CONSTRAINT "interviews_idea_id_ideas_id_fk" FOREIGN KEY ("idea_id") REFERENCES "public"."ideas"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "statements" ADD CONSTRAINT "statements_interview_id_interviews_id_fk" FOREIGN KEY ("interview_id") REFERENCES "public"."interviews"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
CREATE INDEX "ideas_founder_id_idx" ON "ideas" USING btree ("founder_id");--> statement-breakpoint
CREATE INDEX "interviews_idea_id_created_at_idx" ON "interviews" USING btree ("idea_id","created_at");--> statement-breakpoint
CREATE UNIQUE INDEX "statements_interview_position_uq" ON "statements" USING btree ("interview_id","position");