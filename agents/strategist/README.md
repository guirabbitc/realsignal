# valiDate Strategist

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

The last step of the valiDate team. Given an idea and a judged interview, it writes the read-out: what the interview means, why, and the next 3 questions to ask.

It never changes a judgment, the score or the verdict. Those are final when they reach it; it only writes. Any quote in its text that is not word for word in the transcript is dropped.

## How to use it

**In ASI:One:** say hi. It asks what idea the interview tests, then for the transcript. It asks the Signal Analyst agent to judge the interview, then replies with the read-out and the next questions.

**From another agent:** send a `WriteUp` with an already judged interview (see Messages). This is how the valiDate front agent calls it.

For the verdict, quotes and next questions in one reply, talk to **valiDate**.

## Messages

This agent speaks two protocols: `AgentChatProtocol` (chat, for ASI:One) and `ValiDateStrategist` 0.2.0 (typed messages, below).

| Direction | Message | Fields |
| --- | --- | --- |
| Request | `WriteUp` | `idea`, `transcript`, `judged` (the Signal Analyst's result) |
| Reply | `Written` | `result`: the full analysis, with `summary`, `reasons[]` and `next_questions[]` added |
| Reply on failure | `StageError` | `stage`, `error` |

It keeps no data between requests.

## The valiDate team

| Agent | Job | Address |
| --- | --- | --- |
| valiDate | Talks to the founder, plans the steps, merges the answers | `agent1q04gnfnfl0sl0qusvte6rd0gnzhvtvhzpjceugx9p07wuny8lswlvj0g4mn` |
| valiDate Intake | Works out who is the interviewer and who is the customer | `agent1q0exnynml2849c0kmafyth4mem8xgs9fzx5yqmyzep8uc7za7lmyssrqeqq` |
| valiDate Signal Analyst | Judges each customer sentence, scores the interview, picks the verdict | `agent1q08gppxzdjsvrczrmref9gmd96lpawgdwhx6vpdv6vqc688j72rgutk3qar` |
| valiDate Strategist | Writes the read-out and the next questions | `agent1qve9d7cjnn60y8v9ajt5gdz27z0zwvv880q4a04ge3jg4yx2p55hw7hpkqc` |
