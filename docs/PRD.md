# validate.ai: Product Requirements (PRD)

> **Status:** draft v1 · 2026-10-03
> **Authors:** Guilherme Coelho, Murilo Guazzelli
> **Working name:** validate.ai. The final name is still open (see Open Questions).
> **Context:** built for MHacks 2026 (Ann Arbor, Oct 3–4, 2026), Actually Intelligent track and Fetch.ai track. We intend to keep building it as a startup after the hackathon.
> **This document is intent:** the problem, who has it, what we bet, and what we will not do. Engineering decisions (stack, data model, contracts, layout) are in [`SPEC.md`](SPEC.md). Where the two disagree, this file wins on *what* and *why*, and SPEC wins on *how*.

---

## 1. Problem statement

**Who:** first-time and student founders who are running their first customer discovery interviews and product demos, and who have never been taught how to read them.

**The pain:** customers are polite. In interviews and demos they say "cool idea" and "I'd use that" even when they would never pay. A first-time founder hears "yes", counts it as validation, and keeps building. Nobody tells them after the call which things the customer said were real interest and which were politeness.

**The cost of not solving it:** months of time and money spent building something nobody buys. "No market need" is the most common reason founders give for why their startup failed (§2).

**Reframe test:** more than one solution could fit this problem: a mentor who reviews every call, a checklist, a course, a tool. We are betting on one of them (§3). The problem statement doesn't assume it.

## 2. Evidence

| Claim | Evidence | Status |
| --- | --- | --- |
| Building without real demand is the main way startups fail | CB Insights' study of startup post-mortems: **42% named "no market need"** as the main reason, ahead of running out of cash (**29%**). | Evidenced (third-party) |
| The fix is known, but first-time founders don't apply it | The method is well established ("The Mom Test": ask about past behaviour, look for commitments, not compliments). Our claim that founders *don't apply it* comes from our own experience. | **Assumption.** Validate by scoring the first interview of the first 10 founders: how many are mostly hypotheticals and compliments? |
| Founders can't tell polite from real on their own, even after the call | Our own experience as founders. | **Assumption.** Validate by asking founders to guess their own verdict before they see ours, then comparing. |
| Existing tools record and summarise but don't judge | Competitive scan (below). | Evidenced (desk research) |

**How founders cope today, and what each option leaves out:**

| Who | What they do | What they don't do |
| --- | --- | --- |
| Otter, Grain, Dovetail, Nugget | Record, transcribe, summarise and organise interviews | Judge whether the interest was real, or give a verdict |
| Koji, Lùc, MomTestGPT | AI interviews and Mom Test filters | Serve founders deciding what to build (they're aimed at research teams and agencies) |
| Gong, Chorus, Tario | Detect real buying intent vs polite interest | Handle discovery interviews or idea validation (they're built for **sales** calls) |
| ChatGPT / Claude with a prompt | Free, one transcript at a time | Calibrated confidence, history across interviews, coaching on the founder's own habits, or a cohort view |
| A mentor or advisor | Reads the situation with real judgment | Scale, or show up the hour after every call |

## 3. Thesis: why build this, why now, why founders would switch

**Why this:** what a founder needs after a call is a judgment, not a summary: *was this real?* The judgment is only useful if it is **honest**. It must quote the exact words it relied on, and it must be willing to say "not enough evidence yet" instead of guessing.

**Why now:** judgment models that return **calibrated probabilities** (not just generated text) became available in September 2026. They are cheap and fast enough to judge **every sentence** a customer said, not just give the whole conversation a vibe. Transcription is already a commodity.

**Why founders would switch from how they cope today:**

1. **Evidence, not opinion.** Every verdict cites the customer's exact words. A founder can check it in seconds.
2. **Honest uncertainty.** When the evidence is thin, the product says so and tells them what to ask next, instead of inventing a verdict.
3. **It compounds.** Each interview adds to the history for an idea, so the founder sees whether the evidence is getting stronger or weaker. A one-off chat prompt can't do this.
4. **It coaches the founder too.** It points out their own habits that produce polite answers: talking too much, pitching before asking about the problem, leading questions.

**Core principle (non-negotiable):** the judgment, the explanation and the score are three separate jobs. A calibrated model judges each sentence. A writing model explains the result in plain language and **can never change the judgment**. The score is plain arithmetic that anyone can check. (How this is enforced: SPEC §4–5.)

## 4. Hypothesis

> **We believe** that giving first-time founders a verdict with quoted evidence after each interview
> **will cause** them to change their interview questions or their idea sooner than founders who only have notes or a summary,
> **resulting in** less time spent building ideas without real demand.
>
> **We'll know we're RIGHT if** ≥ 40% of founders who analyse 3 or more interviews for the same idea change their questions or their idea within 2 weeks of their first analysis.
>
> **We'll know we're WRONG if** < 15% do, **or** if founders tell us the verdict was wrong about their own interview often enough that they stop trusting it (guardrail; threshold TBD).

The numbers are an **initial guess**. Revisit them after the first 20 founders.

**How "changed their questions or idea" is measured:** TBD, needs validation. Candidates:
(a) the founder edits the idea or creates a new one;
(b) the "pitched early" and "leading questions" signals drop between interview 1 and interview 3;
(c) the founder says so when asked after the 3rd interview.

## 5. Target user and job to be done

**Primary user:** a first-time or student founder who has just finished a discovery interview or a demo. They have a transcript and a feeling ("they loved it").

**Job to be done:**
> When I finish a customer interview and feel good about it, I want to know which things they said were real interest and which were politeness, so I can decide whether to keep going, narrow down, try a new angle or pivot before I spend months building.

**Secondary user (later, not MVP):** accelerators and incubators that want to know which of their startups are working on a real problem.

**Non-users (explicitly not for):**

- Research teams and agencies running large qualitative studies (Dovetail, Koji and others serve them).
- Sales teams qualifying deals (Gong and Chorus serve them).
- Anyone evaluating **a person**: hiring, employee performance, dating (see Non-goals).
- The interviewee. The product talks only to the founder.

**Constraints:**
- English only.
- Transcripts must say who spoke ("Founder:" / "Customer:").
- The interviewee must know the conversation was recorded.

## 6. MVP: the thinnest line that proves or kills the hypothesis

A founder can run the whole loop alone, with no signup, and repeat it across interviews for the same idea:

| # | Capability | What the founder can do |
| --- | --- | --- |
| C1 | **Ideas** | Describe an idea in one sentence (what, and for whom). Keep more than one. |
| C2 | **Interview intake** | Paste a transcript or upload a `.txt` file where each turn is labelled with who spoke. Mark it as an interview or a demo, and label who the interviewee was. |
| C3 | **Sentence-level judgment** | See every sentence the customer said, labelled as a **real signal** or **politeness**, with its kind (commitment, past pain, hypothetical, compliment, neutral) and how sure the judgment is. |
| C4 | **Score and verdict** | Get a 0–100 signal score and one verdict: **keep going**, **narrow down**, **try a new angle**, **pivot**, or **not enough evidence yet**. The last one wins whenever the evidence is thin. |
| C5 | **Read-out** | Read a plain-language explanation of the verdict, the strongest real quotes, the strongest polite quotes, the founder's own mistakes in the interview (talk time, pitching early, leading questions), and the 3 questions to ask next. **Every quote appears word for word in the transcript.** |
| C6 | **History** | See all analysed interviews for an idea, with their verdicts, in one place. |
| C7 | **Chat access** *(hackathon)* | Run the same analysis from the ASI:One chat, through Fetch.ai agents. |

**Identity in the MVP:** no account. Each browser gets its own private space, and a founder only ever sees their own ideas and interviews. Known trade-off: clearing the browser loses access (Open Questions).

**Door check** (for SPEC and for the factory):
- **Two-way doors, just build:** page layout, wording of the read-out, the order of the read-out sections, history views.
- **One-way doors, decide deliberately:**
  - the privacy promise to founders (it can't be taken back once their data has gone somewhere)
  - how the score is calculated, since a change makes old and new interviews incomparable
  - the stored data shape

**Next after the MVP (not now):** audio upload with transcription, a report across all interviews for an idea, a script for the next interview, a follow-up email draft.

## 7. Success metrics

### Demo (MHacks, Oct 4, 2026)

| Metric | Target | How measured |
| --- | --- | --- |
| Polite and real-pain interviews of the same idea get clearly different verdicts | Polite: score < 30, verdict *pivot* or *not enough evidence*. Mixed: score 40–65, verdict *narrow down* or *new angle*. Real pain: score > 70, verdict *keep going*. | The three reference interviews, 3 runs each |
| Every quote is real | 100% of quotes shown appear word for word in the transcript | Automated check on every analysis |
| Stability | The same interview analysed 3 times gets the same verdict, with scores at most 5 points apart | Automated check |
| End to end | Works in the browser and inside ASI:One | Live run |
| Speed | Read-out appears within 2 minutes of submitting | Timed on the deployed app |

### Product (after the hackathon)

| Metric | Target | How measured |
| --- | --- | --- |
| Behaviour change (the hypothesis) | ≥ 40% right / < 15% wrong (§4) | TBD (§4 candidates) |
| Repeat use | TBD | Share of founders who analyse a 2nd and a 3rd interview for the same idea |
| Usefulness | TBD | Share of founders who say the verdict changed what they did next (asked after the 3rd interview) |
| Trust (guardrail) | Unverifiable quotes shown = **0**. Disputed verdicts: TBD | Automated check; founder feedback on each verdict |

## 8. Non-goals

### Never (out of scope permanently)

1. **Judging people.** No hiring, employee performance, dating, or any use where the person being interviewed is the one being evaluated. We judge **statements about a product**, never the person.
2. **Covert analysis.** Nothing recorded or uploaded without the interviewee knowing the conversation was recorded.
3. **Selling, sharing or training on founders' interview data.**
4. **A verdict without evidence.** Never tell a founder their idea is good or bad without quoting the words behind it.
5. **Inferring emotions, personality or protected traits** about the interviewee.

### Not now (later; these may come back)

- Audio and video upload, in-browser recording, call bots.
- Voice tone and facial expression analysis. Note: Hume's Expression Measurement API shut down on June 14, 2026. Alternatives: audEERING, Imentiv.
- Accounts and login beyond the anonymous browser space.
- Payments, subscriptions, accelerator licences, a cohort dashboard.
- Sending emails; calendar or CRM integrations.
- A mobile app; languages other than English.

## 9. Open questions

- [ ] **Final name.** validate.ai is close to an existing tool, ValidatorAI. The repo is called `realsignal`.
- [ ] **Hypothesis numbers.** 40% right / 15% wrong / 2 weeks are initial guesses. Revisit after the first 20 founders.
- [ ] **How to measure "changed their questions or idea"** (§4 candidates a/b/c).
- [ ] **Targets for repeat use, usefulness and disputed verdicts** (§7).
- [ ] **Which writing model writes the read-out.** A fast one is enough, because it only writes.
- [ ] **Founder-mistake thresholds.** At what talk-time share, or what likelihood of pitching early or leading questions, do we call it a mistake?
- [ ] **Consent.** How do we make the "never covert" rule real? Proposed: the founder confirms at upload that the interviewee knew they were recorded.
- [ ] **Privacy promise vs vendors.** Transcripts are sent to the judgment and writing vendors. The judgment vendor does not train on inputs, but its retention period is unspecified; zero retention is enterprise-only. Is that enough for what we promise founders?
- [ ] **Losing the anonymous space.** When does login become necessary? Should a founder be able to export or move their history?
- [ ] **Abuse and cost.** The app is public and has no login, so anyone can run analyses that cost us money. Do we need a per-browser daily cap, and at what number?
- [ ] **Pricing.** AI and ops cost per interview, then a price per founder and per cohort.
- [ ] **Audio in ASI:One.** Can audio uploads reach a Fetch.ai agent through ASI:One? Ask the Fetch mentors.
- [ ] **Where the chat agent runs during the demo**, so it stays online while judges try it.
