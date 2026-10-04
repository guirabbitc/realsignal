import Link from "next/link";

import { Notice } from "@/components/ui/feedback";

export default function NotFound() {
  return (
    <Notice title="This page doesn’t exist.">
      <Link href="/" className="text-[15px] font-bold">
        Go home
      </Link>
    </Notice>
  );
}
