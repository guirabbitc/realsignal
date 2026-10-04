import { NextResponse } from "next/server";
import { createAndAnalyze, listInterviews } from "@/lib/interviews";

const field = (value: FormDataEntryValue | null) => (typeof value === "string" ? value.trim() : "");

export async function GET() {
  return NextResponse.json(await listInterviews());
}

export async function POST(request: Request) {
  const form = await request.formData();
  const ideaTitle = field(form.get("ideaTitle"));
  const ideaDescription = field(form.get("ideaDescription"));
  const title = field(form.get("title")) || "Interview";
  const pasted = field(form.get("transcript"));
  const upload = form.get("file");
  const file = upload instanceof File && upload.size > 0 ? upload : null;

  if (!ideaTitle || !ideaDescription) {
    return NextResponse.json({ error: "The idea needs a title and a description." }, { status: 400 });
  }

  const isText = file ? file.type.startsWith("text/") || /\.(txt|md)$/i.test(file.name) : false;
  const transcript = pasted || (file && isText ? (await file.text()).trim() : "");
  const audio = !transcript && file && !isText ? file : undefined;
  if (!transcript && !audio) {
    return NextResponse.json({ error: "Paste a transcript or upload a transcript or recording." }, { status: 400 });
  }

  const id = await createAndAnalyze({ ideaTitle, ideaDescription, title, transcript: transcript || undefined, audio });
  return NextResponse.redirect(new URL(`/interviews/${id}`, request.url), 303);
}
