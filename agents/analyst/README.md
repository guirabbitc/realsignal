# valiDate Signal Analyst

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

The judging step of the valiDate team. Given an idea and an interview transcript, it decides how much real interest the interview contains.

- Judges every customer sentence as a commitment, past pain, a hypothetical, a compliment or neutral, with the probability that it is a real signal. The judgments come from Jev, a decision model that returns typed answers with calibrated probabilities.
- Computes a signal score from 0 to 100. The arithmetic is done in code, never by a model.
- Picks the verdict: keep going, narrow down, try a new angle or pivot. When the evidence is too thin, it says so instead of guessing.

It judges statements about a product, never the person.

## How to use it

**In ASI:One:** say hi. It asks what idea the interview tests, then for the transcript, and replies with the verdict, the score and every customer sentence with its judgment.

**From another agent:** send a `JudgeTranscript` (see Messages). This is how the valiDate front agent and the Strategist call it.

For the read-out and next questions as well, talk to **valiDate**.

## Messages

This agent speaks two protocols: `AgentChatProtocol` (chat, for ASI:One) and `ValiDateAnalyst` 0.2.0 (typed messages, below).

| Direction | Message | Fields |
| --- | --- | --- |
| Request | `JudgeTranscript` | `idea`, `transcript` (turns labelled `Founder:` / `Customer:`) |
| Reply | `Judgement` | `judged`: `statements[]` (`position`, `quote`, `category`, `p_real`, `confidence`), `score`, `verdict`, `verdict_confidence`, founder flags, `missing_evidence` |
| Reply on failure | `StageError` | `stage`, `error` |

It keeps no data between requests.

## The valiDate team

| Agent | Job | Address |
| --- | --- | --- |
| valiDate | Talks to the founder, plans the steps, merges the answers | `agent1q04gnfnfl0sl0qusvte6rd0gnzhvtvhzpjceugx9p07wuny8lswlvj0g4mn` |
| valiDate Intake | Works out who is the interviewer and who is the customer | `agent1q0exnynml2849c0kmafyth4mem8xgs9fzx5yqmyzep8uc7za7lmyssrqeqq` |
| valiDate Signal Analyst | Judges each customer sentence, scores the interview, picks the verdict | `agent1q08gppxzdjsvrczrmref9gmd96lpawgdwhx6vpdv6vqc688j72rgutk3qar` |
| valiDate Strategist | Writes the read-out and the next questions | `agent1qve9d7cjnn60y8v9ajt5gdz27z0zwvv880q4a04ge3jg4yx2p55hw7hpkqc` |
