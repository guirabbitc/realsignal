# Decisions

<!-- A decision is asked once. Humans move entries from Open to Answered; never delete an answered one.
     Read order for any node about to stop: answered here? use it and cite the ID. Open here? reference the ID, don't re-ask. -->

## Open

- **D2**: Founder-mistake thresholds (talk ratio, pitched early, leading questions)?
  - **Recommended:** 0.5 each, revisited after 20 real interviews.
  - **Raised:** 2026-10-04 (MISSION Q2). Note: these live in `rubric.json`, so changing them is a judgement value and needs a human.
- **D3**: Does upload require a consent confirmation?
  - **Recommended:** yes, a required checkbox: "The interviewee knew this conversation was recorded."
  - **Raised:** 2026-10-04 (MISSION Q3)
- **D4**: Is there a per-browser daily analysis cap?
  - **Recommended:** TBD after measuring the cost of one analysis.
  - **Raised:** 2026-10-04 (MISSION Q4)
- **D5**: Where does the ASI:One agent run during judging?
  - **Recommended:** a laptop that stays on for the demo window.
  - **Raised:** 2026-10-04 (MISSION Q5)
- **D6**: Where does the factory run, and what is the escalation channel?
  - **Recommended:** decide after MHacks.
  - **Raised:** 2026-10-04 (interview Round 3)

## Answered

- **D1**: Which OpenAI model writes the read-out?
  - **Answer:** `gpt-4.1-nano` for now (`OPENAI_MODEL`).
  - **Decided:** 2026-10-04 by the team. All 3 fixtures passed 3 runs each with it.

- **D0**: Product name in docs.
  - **Answer:** validate.ai (working name; final name still open).
  - **Decided:** 2026-10-04 by the team.
- **D-identity**: How is a founder identified in the MVP?
  - **Answer:** an anonymous signed-cookie session, one founder per browser.
  - **Decided:** 2026-10-04 by the team. See SPEC §7.
- **D-jev-version**: Which Jev model?
  - **Answer:** pinned `jev-1.13.0`; a change is a rubric change.
  - **Decided:** 2026-10-04 by the team. See SPEC §0.1.
- **D-verdict-stability**: How is the verdict made stable?
  - **Answer:** the mean of 3 Jev verdict calls.
  - **Decided:** 2026-10-04 by the team. See SPEC §0.2.
- **D-work-intake**: Where does work arrive?
  - **Answer:** cards on the validate.ai build board (a Claude artifact), not GitHub issues.
  - **Decided:** 2026-10-04 by the team.
