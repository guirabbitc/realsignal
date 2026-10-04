import type { Metadata } from "next";
import { connection } from "next/server";

import { UploadForm } from "@/components/upload/UploadForm";
import { audioConfig } from "@/lib/audio-config";

export const metadata: Metadata = { title: "Add an interview · valiDate" };

export default async function UploadPage(props: PageProps<"/ideas/[id]/upload">) {
  const { id } = await props.params;
  // The audio switches are read per request, never baked in at build time.
  await connection();
  return <UploadForm key={id} ideaId={id} audio={audioConfig()} />;
}
