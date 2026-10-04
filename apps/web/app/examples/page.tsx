import type { Metadata } from "next";

import { ExamplesGallery } from "@/components/examples/ExamplesGallery";

export const metadata: Metadata = { title: "Examples · valiDate" };

export default function ExamplesPage() {
  return <ExamplesGallery />;
}
