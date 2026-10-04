# valiDate Intake

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

The first step of the valiDate team. It gets a customer interview ready for analysis: it works out who is the interviewer and who is the customer, and labels every turn `Founder:` or `Customer:`. Only the labels change; every word that was said is kept exactly.

## How to use it

**In ASI:One:** paste a transcript, with every turn starting with the speaker's name and a colon. It replies with the labelled transcript and says how it mapped the speakers.

**From another agent:** send an `IntakeRequest` (see Messages). This is how the valiDate front agent calls it.

For a verdict on an interview, talk to **valiDate**.

## Messages

This agent speaks two protocols: `AgentChatProtocol` (chat, for ASI:One) and `ValiDateIntake` 0.2.0 (typed messages, below).

| Direction | Message | Fields |
| --- | --- | --- |
| Request | `IntakeRequest` | `text` |
| Reply | `TranscriptReady` | `transcript`, `note` (how the speakers were mapped) |
| Reply on failure | `StageError` | `stage`, `error` |

It keeps no data between requests.

## The valiDate team

| Agent | Job | Address |
| --- | --- | --- |
| valiDate | Talks to the founder, plans the steps, merges the answers | `agent1q04gnfnfl0sl0qusvte6rd0gnzhvtvhzpjceugx9p07wuny8lswlvj0g4mn` |
| valiDate Intake | Works out who is the interviewer and who is the customer | `agent1q0exnynml2849c0kmafyth4mem8xgs9fzx5yqmyzep8uc7za7lmyssrqeqq` |
| valiDate Signal Analyst | Judges each customer sentence, scores the interview, picks the verdict | `agent1q08gppxzdjsvrczrmref9gmd96lpawgdwhx6vpdv6vqc688j72rgutk3qar` |
| valiDate Strategist | Writes the read-out and the next questions | `agent1qve9d7cjnn60y8v9ajt5gdz27z0zwvv880q4a04ge3jg4yx2p55hw7hpkqc` |
