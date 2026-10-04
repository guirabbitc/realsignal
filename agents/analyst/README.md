# ValiDate Signal Analyst

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

The judging step of the ValiDate team. Given an idea and an interview transcript, it decides how much evidence of real demand the interview contains.

- Splits the transcript into sentences and works out who the interviewee is.
- Labels each interviewee sentence as `real_signal`, `polite` or `neutral`, with a confidence from 0 to 1. The labels come from Jev, a decision model that returns typed answers with calibrated probabilities.
- Computes a score from 0 to 100 from those labels. The arithmetic is done in code, never by a model.
- Picks the verdict: `keep_going`, `narrow_down`, `try_new_angle` or `pivot`.

It measures evidence of demand in what was said. It does not judge whether anyone is being honest.

This agent is called by the ValiDate front agent. It has no chat interface: to analyze an interview, talk to **ValiDate**.

## Messages

Protocol: `ValiDateAnalyst` 0.1.0

| Direction | Message | Fields |
| --- | --- | --- |
| Request | `JudgeTranscript` | `idea`, `transcript` |
| Reply | `Judged` | `judged`: `transcript`, `sentences[]` (`order`, `speaker`, `text`, `is_interviewee`, `label`, `confidence`), `score`, `verdict` |
| Reply on failure | `StageError` | `stage`, `error` |

It keeps no data between requests.

## The ValiDate team

| Agent | Job | Address |
| --- | --- | --- |
| ValiDate | Talks to the founder in ASI:One, plans the steps, merges the answers | `agent1q04gnfnfl0sl0qusvte6rd0gnzhvtvhzpjceugx9p07wuny8lswlvj0g4mn` |
| ValiDate Intake | Turns what the founder sent into a clean transcript | `agent1q0exnynml2849c0kmafyth4mem8xgs9fzx5yqmyzep8uc7za7lmyssrqeqq` |
| ValiDate Signal Analyst | Labels each sentence, scores the interview, picks the verdict | `agent1q08gppxzdjsvrczrmref9gmd96lpawgdwhx6vpdv6vqc688j72rgutk3qar` |
| ValiDate Strategist | Writes the summary and next steps | `agent1qve9d7cjnn60y8v9ajt5gdz27z0zwvv880q4a04ge3jg4yx2p55hw7hpkqc` |
