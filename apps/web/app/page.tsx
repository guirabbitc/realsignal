import Link from "next/link";
import { listInterviews } from "@/lib/interviews";
import { VERDICT_TEXT } from "@/lib/labels";

export const dynamic = "force-dynamic";

export default async function Home() {
  const interviews = await listInterviews();
  return (
    <>
      <section>
        <h1>Analyze an interview</h1>
        <form action="/api/interviews" method="post" encType="multipart/form-data">
          <label>
            Idea
            <input name="ideaTitle" required placeholder="Dinner planner" />
          </label>
          <label>
            What the idea is
            <textarea name="ideaDescription" required rows={2} placeholder="An app that plans a week of dinners and orders the groceries." />
          </label>
          <label>
            Interview name
            <input name="title" placeholder="Call with Priya" />
          </label>
          <label>
            Transcript
            <textarea name="transcript" rows={8} placeholder={"Interviewer: How do you plan dinner today?\nPriya: Every Sunday I spent two hours on a spreadsheet."} />
          </label>
          <label>
            Or upload a transcript (.txt or .pdf) or a recording
            <input type="file" name="file" accept=".txt,.md,.pdf,text/plain,application/pdf,audio/*,video/*" />
          </label>
          <button type="submit">Analyze</button>
        </form>
      </section>

      <section>
        <h2>Recent interviews</h2>
        {interviews.length === 0 ? (
          <p className="muted">None yet.</p>
        ) : (
          <ul className="list">
            {interviews.map((i) => (
              <li key={i.id}>
                <Link href={`/interviews/${i.id}`}>{i.title}</Link>
                <span className="muted"> · {i.ideaTitle}</span>
                <span className={`status ${i.status}`}>
                  {i.status === "done" && i.verdict ? `${VERDICT_TEXT[i.verdict]} · ${i.score}` : i.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  );
}
