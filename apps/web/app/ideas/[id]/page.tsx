import type { Metadata } from "next";

import { IdeaHistory } from "@/components/ideas/IdeaHistory";

export const metadata: Metadata = { title: "Idea · valiDate" };

export default async function IdeaPage(props: PageProps<"/ideas/[id]">) {
  const { id } = await props.params;
  return <IdeaHistory key={id} ideaId={id} />;
}
