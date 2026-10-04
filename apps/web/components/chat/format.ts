// The agents reply in a small subset of markdown. This turns a reply into blocks the chat can draw,
// without a markdown dependency.

export type Block =
  | { kind: "heading"; text: string }
  | { kind: "note"; text: string }
  | { kind: "paragraph"; text: string }
  | { kind: "bullets"; items: string[] }
  | { kind: "steps"; items: string[] };

/** Drops inline markers the chat does not style: `code` ticks and **bold** inside a line. */
function plain(text: string): string {
  return text.replace(/`([^`]+)`/g, "$1").replace(/\*\*([^*]+)\*\*/g, "$1").trim();
}

export function formatReply(reply: string): Block[] {
  const blocks: Block[] = [];
  for (const raw of reply.split("\n")) {
    const line = raw.trim();
    if (!line) continue;
    const last = blocks.at(-1);
    const heading = line.match(/^\*\*(.+)\*\*$/);
    const note = line.match(/^_(.+)_$/);
    const bullet = line.match(/^- (.+)$/);
    const step = line.match(/^\d+\. (.+)$/);
    if (heading) blocks.push({ kind: "heading", text: plain(heading[1]) });
    else if (note) blocks.push({ kind: "note", text: plain(note[1]) });
    else if (bullet && last?.kind === "bullets") last.items.push(plain(bullet[1]));
    else if (bullet) blocks.push({ kind: "bullets", items: [plain(bullet[1])] });
    else if (step && last?.kind === "steps") last.items.push(plain(step[1]));
    else if (step) blocks.push({ kind: "steps", items: [plain(step[1])] });
    else blocks.push({ kind: "paragraph", text: plain(line) });
  }
  return blocks;
}
