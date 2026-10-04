CREATE TYPE "public"."interview_source" AS ENUM('transcript', 'audio');--> statement-breakpoint
CREATE TYPE "public"."interview_status" AS ENUM('processing', 'done', 'failed');--> statement-breakpoint
CREATE TYPE "public"."signal_label" AS ENUM('real_signal', 'polite', 'neutral');--> statement-breakpoint
CREATE TYPE "public"."verdict" AS ENUM('keep_going', 'narrow_down', 'try_new_angle', 'pivot');--> statement-breakpoint
CREATE TABLE "analyses" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"interview_id" uuid NOT NULL,
	"score" real NOT NULL,
	"verdict" "verdict" NOT NULL,
	"summary" text NOT NULL,
	"next_steps" jsonb NOT NULL,
	"raw" jsonb NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "analyses_interview_id_unique" UNIQUE("interview_id")
);
--> statement-breakpoint
CREATE TABLE "founders" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"email" text NOT NULL,
	"name" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	CONSTRAINT "founders_email_unique" UNIQUE("email")
);
--> statement-breakpoint
CREATE TABLE "ideas" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"founder_id" uuid NOT NULL,
	"title" text NOT NULL,
	"description" text NOT NULL,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "interviews" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"idea_id" uuid NOT NULL,
	"title" text NOT NULL,
	"source" "interview_source" NOT NULL,
	"transcript" text,
	"status" "interview_status" DEFAULT 'processing' NOT NULL,
	"error" text,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL,
	"updated_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
CREATE TABLE "signals" (
	"id" uuid PRIMARY KEY DEFAULT gen_random_uuid() NOT NULL,
	"interview_id" uuid NOT NULL,
	"order" integer NOT NULL,
	"speaker" text NOT NULL,
	"text" text NOT NULL,
	"is_interviewee" boolean NOT NULL,
	"label" "signal_label",
	"confidence" real,
	"created_at" timestamp with time zone DEFAULT now() NOT NULL
);
--> statement-breakpoint
ALTER TABLE "analyses" ADD CONSTRAINT "analyses_interview_id_interviews_id_fk" FOREIGN KEY ("interview_id") REFERENCES "public"."interviews"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "ideas" ADD CONSTRAINT "ideas_founder_id_founders_id_fk" FOREIGN KEY ("founder_id") REFERENCES "public"."founders"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "interviews" ADD CONSTRAINT "interviews_idea_id_ideas_id_fk" FOREIGN KEY ("idea_id") REFERENCES "public"."ideas"("id") ON DELETE cascade ON UPDATE no action;--> statement-breakpoint
ALTER TABLE "signals" ADD CONSTRAINT "signals_interview_id_interviews_id_fk" FOREIGN KEY ("interview_id") REFERENCES "public"."interviews"("id") ON DELETE cascade ON UPDATE no action;