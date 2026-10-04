import { notFound } from "next/navigation";
import { getInterview } from "@/lib/interviews";
import { LABEL_TEXT, VERDICT_TEXT } from "@/lib/labels";

export const dynamic = "force-dynamic";

export default async function InterviewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  if (!/^[0-9a-f-]{36}$/i.test(id)) notFound();
  const data = await getInterview(id);
  if (!data) notFound();
  const { interview, idea, sentences, analysis } = data;

  return (
    <>
      <section>
        <p className="muted">{idea.title}</p>
        <h1>{interview.title}</h1>
        <p className={`status ${interview.status}`} data-testid="status">{interview.status}</p>
        {interview.status === "failed" && <p className="error">{interview.error}</p>}
        {interview.status === "processing" && <p className="muted">Still processing. Reload in a moment.</p>}
      </section>

      {analysis && (
        <section className="verdict">
          <div>
            <span className="muted">Verdict</span>
            <strong data-testid="verdict">{VERDICT_TEXT[analysis.verdict]}</strong>
          </div>
          <div>
            <span className="muted">Demand score</span>
            <strong data-testid="score">{analysis.score} / 100</strong>
          </div>
        </section>
      )}

      {analysis && (
        <section>
          <h2>Summary</h2>
          <p>{analysis.summary}</p>
          <h2>Next steps</h2>
          <ol>
            {analysis.nextSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ol>
        </section>
      )}

      {sentences.length > 0 && (
        <section>
          <h2>Sentences</h2>
          <ul className="sentences">
            {sentences.map((s) => (
              <li key={s.id} className={s.label ?? "interviewer"}>
                <span className="speaker">{s.speaker}</span>
                <span className="text">{s.text}</span>
                {s.label && (
                  <span className="label">
                    {LABEL_TEXT[s.label]} · {Math.round((s.confidence ?? 0) * 100)}%
                  </span>
                )}
              </li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
