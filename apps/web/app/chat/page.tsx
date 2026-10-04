import type { Metadata } from "next";

import { AgentChat } from "@/components/chat/AgentChat";

export const metadata: Metadata = { title: "Chat with the agents · valiDate" };

export default function ChatPage() {
  return <AgentChat />;
}
