# ValiDate Intake

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

The first step of the ValiDate team. It takes whatever the founder sent and returns a clean interview transcript with one `Speaker: words` turn per line.

- Pasted or uploaded text is passed on as the transcript.
- A PDF is read and its text extracted.
- A recording is transcribed with speaker labels.

This agent is called by the ValiDate front agent. It has no chat interface: to analyze an interview, talk to **ValiDate**.

## Messages

Protocol: `ValiDateIntake` 0.1.0

| Direction | Message | Fields |
| --- | --- | --- |
| Request | `IntakeRequest` | `text` (optional), `audio_b64` (optional, a PDF or recording as base64), `filename`, `mime_type` |
| Reply | `TranscriptReady` | `transcript` |
| Reply on failure | `StageError` | `stage`, `error` |

It keeps no data between requests.

## The ValiDate team

| Agent | Job | Address |
| --- | --- | --- |
| ValiDate | Talks to the founder in ASI:One, plans the steps, merges the answers | `agent1q04gnfnfl0sl0qusvte6rd0gnzhvtvhzpjceugx9p07wuny8lswlvj0g4mn` |
| ValiDate Intake | Turns what the founder sent into a clean transcript | `agent1q0exnynml2849c0kmafyth4mem8xgs9fzx5yqmyzep8uc7za7lmyssrqeqq` |
| ValiDate Signal Analyst | Labels each sentence, scores the interview, picks the verdict | `agent1q08gppxzdjsvrczrmref9gmd96lpawgdwhx6vpdv6vqc688j72rgutk3qar` |
| ValiDate Strategist | Writes the summary and next steps | `agent1qve9d7cjnn60y8v9ajt5gdz27z0zwvv880q4a04ge3jg4yx2p55hw7hpkqc` |
