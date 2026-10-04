<!-- Paste everything below this line into another LLM. Replace {N} (10 to 12 works well) and the
     last line. Save the JSON it returns as a file in evals/cases/, then run: uv run python -m evals.run -->

I'm testing a tool called ValiDate. It reads a transcript of a customer interview, where a founder asks a potential customer about a startup idea, and judges how much evidence of real demand the interview contains. I need you to write test cases for it: realistic interviews where you decide the right answer in advance, so I can compare the tool's output with yours and measure its accuracy.

Please write {N} test cases. Each one is a startup idea, an interview about it, and your answer key.

## What the tool decides

For each sentence the interviewee says, the tool assigns one label:

- real_signal: evidence of real demand. Something the person already did, paid, lost or tried, or a concrete commitment of money, time or reputation. Examples: "Last month I paid $60 for a meal kit." "Send me the invoice today." "I'll introduce you to my manager on Friday."
- polite: politeness without evidence. Compliments, enthusiasm, and hypothetical statements about what they would or might do. Examples: "I love it." "I would definitely use that." "My friends would be into this."
- neutral: neither. Plain facts, small talk, or statements that say nothing about demand. Examples: "I work in logistics." "I usually cook on Sundays."

Then it gives the whole interview one verdict:

- keep_going: strong evidence of demand for this idea as it is.
- narrow_down: real evidence, but only for one part of the idea or one kind of customer.
- try_new_angle: the person has a real problem, but it is not the problem this idea solves.
- pivot: little or no evidence of demand beyond politeness.

The distinction that matters is between what people have done and what they say they would do. The tool measures evidence of demand. It does not judge whether anyone is being honest, so don't write interviewees who are lying.

## Personas

Give each interviewee one of these personas. The persona is the answer key for the verdict.

| Persona | How they talk | Expected verdict |
|---|---|---|
| committed_buyer | Describes money and time already spent on the problem, failed workarounds, and makes concrete commitments | keep_going |
| polite_enthusiast | Warm and encouraging, full of compliments and "I would", but no past behavior and no commitment | pivot |
| indifferent | Not rude, but the problem barely affects them; short factual answers, mild politeness | pivot |
| advice_giver | Talks about what other people would want and gives product advice, with nothing about their own behavior | pivot |
| partial_fit | Real, costly pain for one specific part of the idea; shrugs at the rest | narrow_down |
| wrong_segment_right_pain | The idea targets a broad group; this person shows real demand, but clearly only because of a narrow situation they are in | narrow_down |
| adjacent_pain | Real, costly pain and even commitment, but for a different problem than the idea solves | try_new_angle |
| mixed_signals | Some genuine past behavior, plus a lot of politeness and hedging; no commitment | You decide, and explain why |

Use each persona at least once if {N} allows, and spread the cases evenly across the four verdicts.

## Make them realistic and hard

Easy cases teach me nothing. Aim for roughly one third easy, one third medium and one third hard, and say which is which.

What makes a case hard:

- Enthusiastic language around a real commitment, or flat language around strong evidence. Tone and evidence should not always match.
- A statement that sounds like past behavior but is hypothetical ("I'd have paid for that last year"), or sounds hypothetical but is a commitment ("I would sign today, send it over").
- Past behavior that points away from the idea ("I tried three apps like this and stopped using all of them").
- A real commitment that is small, next to a large compliment.
- Evidence about someone else ("my sister spends hours on this") rather than the speaker.

Vary the ideas widely: consumer apps, B2B software, hardware, services, marketplaces, different industries and different kinds of customers. Vary how people speak: terse, rambling, formal, casual. Don't reuse names.

## Format rules for the transcript

The tool parses the transcript mechanically, so these rules matter:

- One speaker turn per line, written as `Name: words`. Use `Interviewer` for the founder and a first name for the interviewee.
- Each interviewee line holds exactly one sentence, ending in a period, question mark or exclamation mark. If the interviewee says three sentences in a row, write three lines.
- Interviewer lines can hold more than one sentence.
- Inside interviewee sentences, avoid abbreviations that end in a period ("Dr.", "e.g.", "etc."), because the tool splits sentences at periods. Numbers like 4.50 are fine.
- The interviewer asks the questions. The interviewee asks at most one.
- 10 to 16 interviewee lines per interview. The interviewer's first line should mention the idea naturally.
- No stage directions, timestamps or notes inside the transcript.

## Output

Return only a JSON array, with no text before or after it. Each element:

```json
{
  "id": "case-01",
  "idea": "One or two sentences describing the startup idea.",
  "persona": "one of the persona names above",
  "difficulty": "easy | medium | hard",
  "expected_verdict": "keep_going | narrow_down | try_new_angle | pivot",
  "why": "Two or three sentences: what in the interview justifies this verdict, and for hard cases, what makes it tricky.",
  "transcript": "Interviewer: ...\nMaya: ...\nMaya: ...\nInterviewer: ...",
  "interviewee_sentences": [
    {"text": "The exact sentence, copied from the transcript.", "label": "real_signal | polite | neutral"}
  ]
}
```

`interviewee_sentences` must list every interviewee line, in order, with the text copied exactly as it appears in the transcript. Do not include interviewer lines.

Before you answer, check each case: the labels you assigned should actually support the verdict you chose. If an interview you wrote as keep_going turns out to have mostly polite sentences, rewrite the interview, not the answer key.

Focus this batch on: {optional: an industry, a persona, or "hard cases only"}
