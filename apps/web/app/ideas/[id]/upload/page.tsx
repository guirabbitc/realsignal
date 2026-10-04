import type { Metadata } from "next";

import { UploadForm } from "@/components/upload/UploadForm";

export const metadata: Metadata = { title: "Add an interview · valiDate" };

export default async function UploadPage(props: PageProps<"/ideas/[id]/upload">) {
  const { id } = await props.params;
  return <UploadForm key={id} ideaId={id} />;
}
