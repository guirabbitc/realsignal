<!-- Paste everything below this line into another LLM. It returns 10 cases per reply; say "next" twice
     to get all 30. Save each reply as its own file in agents/tester/cases/ (for example gpt-1.json,
     gpt-2.json, gpt-3.json), then run: uv run --project agents python agents/tester/agent.py -->

I'm testing a tool called valiDate. It reads the transcript of a customer discovery interview, where a founder asks a potential customer about a startup idea, and judges how much real interest the interview contains. I need you to write test cases for it: realistic interviews where you decide the right answer in advance, so I can compare the tool's output with yours and measure its accuracy.

Please write 30 test cases in total, 10 per reply. Each case is a startup idea, an interview about it, and your answer key. In this reply, return cases 01 to 10. When I say "next", return the next 10, continuing the numbering and the plan below without repeating ideas, industries or names.

## What the tool decides

**1. A category for every sentence the customer says:**

- commitment: a concrete next step the customer commits to: a pilot, a meeting, money, an introduction, a date. "Send me the pilot link and I'll set it up on Monday."
- past_pain: something the customer already did, paid, lost or worked around in the past because of this problem. "I pay someone 300 dollars a month just to reply to booking messages."
- hypothetical: what the customer says they would, might or could do in the future, with nothing behind it. "I'd probably try it."
- compliment: praise or enthusiasm about the idea or the founder, with no evidence of need. "That's a really smart idea."
- neutral: a fact, context or small talk that says nothing about interest either way. "We have about twelve tables."

commitment and past_pain are real signals. hypothetical and compliment are politeness. The distinction that matters is between what people have done or commit to, and what they say they would do.

**2. One verdict for the whole interview:**

- keep_going: the evidence shows real pain or commitment for this idea and this customer.
- narrow_down: there is some real signal, but only for part of the idea or a narrower kind of customer.
- new_angle: the pain looks real, but this solution or framing is not landing.
- pivot: the interest is mostly politeness, with no real pain or commitment.
- need_more_evidence: the interview is too thin to judge. The tool gives this verdict, whatever was said, when the customer says fewer than 150 words in total or fewer than 4 of their sentences are non-neutral.

**3. Three checks on the founder's own interviewing:**

- pitched_early: the founder described the product before asking about the problem.
- leading_questions: the founder asked questions that suggest the answer they want ("Wouldn't that save you a lot of time?").
- talked_too_much: the founder said more words than the customer.

The tool judges statements about a product, never the person, and never whether anyone is being honest. Don't write customers who are lying.

## Personas

Give each customer one of these personas. The persona decides the expected verdict.

| Persona | How the customer talks | Expected verdict |
|---|---|---|
| committed_buyer | Money and time already spent on the problem, failed workarounds, and a concrete commitment | keep_going |
| pain_without_commitment | Strong, costly past pain with this exact problem, but no commitment is asked for or given | keep_going (narrow_down also allowed) |
| partial_fit | Real, costly pain for one specific part of the idea; indifferent to the rest | narrow_down |
| narrow_segment | Real demand, but clearly only because of a special situation that most of the idea's target customers are not in | narrow_down |
| solution_miss | The pain is real and costly, but they push back on this solution: wrong format, wrong channel, would not fit how they work | new_angle |
| adjacent_pain | Real, costly pain and even commitment, but about a different problem than the one the idea solves | new_angle |
| polite_enthusiast | Warm and encouraging, full of compliments and "I would", with no past behaviour and no commitment | pivot |
| advice_giver | Talks about what other people would want and gives product advice, with nothing about their own behaviour | pivot |
| thin_evidence | Short or evasive: mostly neutral facts, few words | need_more_evidence |
| mixed_signals | Some real past behaviour, plus a lot of politeness and hedging; no commitment | You decide; list every verdict you would accept |

## The plan for all 30 cases

Verdicts: 7 keep_going, 7 narrow_down, 7 new_angle, 6 pivot, 3 need_more_evidence. Spread them across the three replies, so each reply has every verdict at least once except need_more_evidence, which appears once per reply.

Use every persona at least twice across the 30.

Difficulty: 10 easy, 10 medium, 10 hard. What makes a case hard:

- Tone and evidence do not match: enthusiastic language around a real commitment, or flat language around strong evidence.
- A sentence that sounds like past behaviour but is hypothetical ("I'd have paid for that last year"), or sounds hypothetical but is a commitment ("I would sign today, send it over").
- Past behaviour that points away from the idea ("I tried three apps like this and stopped using all of them").
- A small real commitment next to a large compliment.
- Evidence about someone else ("my sister spends hours on this") rather than the speaker.

Founder behaviour: in about a third of the cases the founder interviews well (asks about the past, does not pitch). In the rest, make one or two of the three founder mistakes clearly visible. Keep the founder's mistakes independent of the verdict: a founder can pitch early to a committed buyer.

Ideas: vary them widely across consumer apps, B2B software, hardware, services and marketplaces, in different industries and for different kinds of customers. Vary how customers speak: terse, rambling, formal, casual.

## Format rules for the transcript

The tool parses the transcript mechanically, so these rules matter:

- Every line starts with exactly `Founder:` or `Customer:`. No other speaker labels, no names.
- Each `Customer:` line holds exactly one sentence, ending in a period, question mark or exclamation mark. If the customer says three sentences in a row, write three `Customer:` lines.
- `Founder:` lines can hold more than one sentence.
- Inside customer sentences, avoid abbreviations that end in a period ("Dr.", "e.g.", "etc."), because the tool splits sentences at periods. Numbers like 4.50 are fine.
- 12 to 18 customer lines per interview, and at least 180 customer words in total, so the interview clears the 150-word minimum with room to spare. Count them. The only exception is the thin_evidence persona: 5 to 8 customer lines, under 120 customer words in total, and at most 3 non-neutral sentences.
- Every case except thin_evidence needs at least 5 non-neutral customer sentences. A pivot case needs them too: they are hypothetical and compliment sentences.
- For talked_too_much: true, the founder's lines must clearly add up to more words than the customer's. For false, clearly fewer.
- The idea is one sentence, under 300 characters.
- No stage directions, timestamps, blank lines or notes inside the transcript.

## Output

Return only a JSON array of 10 elements, with no text before or after it. Each element:

```json
{
  "id": "case-01",
  "idea": "One sentence describing the startup idea and who it is for.",
  "persona": "one of the persona names above",
  "difficulty": "easy | medium | hard",
  "expected_verdict": "keep_going | narrow_down | new_angle | pivot | need_more_evidence",
  "allowed_verdicts": ["every verdict you would accept as correct, including expected_verdict"],
  "why": "Two or three sentences: what in the interview justifies this verdict, and for hard cases, what makes it tricky.",
  "founder": {"pitched_early": false, "leading_questions": true, "talked_too_much": false},
  "transcript": "Founder: ...\nCustomer: ...\nCustomer: ...\nFounder: ...",
  "customer_sentences": [
    {"text": "The exact sentence, copied from the transcript without the Customer: label.", "category": "commitment | past_pain | hypothetical | compliment | neutral"}
  ]
}
```

`customer_sentences` must list every `Customer:` line, in order, with the text copied exactly as it appears in the transcript. Do not include founder lines.

`allowed_verdicts` usually holds only the expected verdict. Add a second one only where two verdicts are both defensible, as in the persona table.

Before you answer, check each case:

- The categories you assigned support the verdict you chose. If an interview you wrote as keep_going turns out to have mostly polite sentences, rewrite the interview, not the answer key.
- The customer word count and the number of non-neutral sentences match the rules above for that persona.
- Every `text` in `customer_sentences` appears word for word in the transcript.
