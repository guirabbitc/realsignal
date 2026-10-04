import { NextResponse } from "next/server";
import { getInterview } from "@/lib/interviews";

export async function GET(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/i.test(id)) return NextResponse.json({ error: "Not found" }, { status: 404 });
  const interview = await getInterview(id);
  if (!interview) return NextResponse.json({ error: "Not found" }, { status: 404 });
  return NextResponse.json(interview);
}
