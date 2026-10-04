import type { Metadata } from "next";

import { IdeasList } from "@/components/ideas/IdeasList";

export const metadata: Metadata = { title: "My ideas · valiDate" };

export default function IdeasPage() {
  return <IdeasList />;
}
