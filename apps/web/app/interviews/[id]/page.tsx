import type { Metadata } from "next";

import { ReadOut } from "@/components/read-out/ReadOut";

export const metadata: Metadata = { title: "Read-out · valiDate" };

// The read-out loads in the browser: the API scopes it to the session cookie and the page polls it.
export default async function InterviewPage(props: PageProps<"/interviews/[id]">) {
  const { id } = await props.params;
  return <ReadOut key={id} id={id} />;
}
