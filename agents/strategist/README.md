# ValiDate Strategist

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

The last step of the ValiDate team. Given an idea and a judged interview, it writes what the founder should take away and do next.

- A summary that explains the verdict using the interviewee's own sentences as evidence.
- Three to five concrete next steps, such as what to ask in the next interview or what commitment to ask for.

It never changes a label, the score or the verdict. Those are final when they reach it; it only writes.

## How to use it

**In ASI:One:** say hi. It asks what idea the interview tests, then for the transcript. It asks the Signal Analyst agent to judge the interview, then replies with the summary and next steps.

**From another agent:** send a `WriteUp` with an already judged interview (see Messages). This is how the ValiDate front agent calls it.

For the verdict, quotes and next steps in one reply, talk to **ValiDate**.

## Messages

This agent speaks two protocols: `AgentChatProtocol` (chat, for ASI:One) and `ValiDateStrategist` 0.1.0 (typed messages, below).

| Direction | Message | Fields |
| --- | --- | --- |
| Request | `WriteUp` | `idea`, `judged` (the Signal Analyst's result) |
| Reply | `Written` | `written`: `summary`, `next_steps[]` |
| Reply on failure | `StageError` | `stage`, `error` |

It keeps no data between requests.

## The ValiDate team

| Agent | Job | Address |
| --- | --- | --- |
| ValiDate | Talks to the founder in ASI:One, plans the steps, merges the answers | `agent1q04gnfnfl0sl0qusvte6rd0gnzhvtvhzpjceugx9p07wuny8lswlvj0g4mn` |
| ValiDate Intake | Turns what the founder sent into a clean transcript | `agent1q0exnynml2849c0kmafyth4mem8xgs9fzx5yqmyzep8uc7za7lmyssrqeqq` |
| ValiDate Signal Analyst | Labels each sentence, scores the interview, picks the verdict | `agent1q08gppxzdjsvrczrmref9gmd96lpawgdwhx6vpdv6vqc688j72rgutk3qar` |
| ValiDate Strategist | Writes the summary and next steps | `agent1qve9d7cjnn60y8v9ajt5gdz27z0zwvv880q4a04ge3jg4yx2p55hw7hpkqc` |
