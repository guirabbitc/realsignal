# ValiDate

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

ValiDate reads a customer interview and tells a founder how much evidence of real demand is in it.

People are polite in interviews. "Cool idea, I'd use that" feels like validation, but it is not evidence. ValiDate separates what people actually did, paid for or committed to from compliments and hypotheticals.

## What you get

- Each interviewee sentence labelled real signal, polite or neutral, with a confidence
- A score from 0 to 100 for how much real demand the interview shows
- A verdict: keep going, narrow down, try a new angle, or pivot
- The strongest quotes behind the verdict
- Concrete next steps for your next interview

## How to use it

1. Say hi. ValiDate asks what idea you are testing; answer in one sentence.
2. Paste the interview transcript. One "Speaker: words" turn per line works best.

You can send more interviews for the same idea, or write `new idea: ...` to test another one.

**Example**

> An app that plans a week of dinners and orders the groceries.

> Interviewer: How do you plan dinner today?
> Priya: Every Sunday I spent two hours building a spreadsheet of meals.
> Priya: I will pay for the first month right now if you can set it up this week.

## How it works

ValiDate is a team of four agents. This one plans the work and talks to you. It hands the interview to Intake, then to the Signal Analyst, then to the Strategist, and merges their answers into one reply. If a teammate does not answer, it finishes the job itself. Each teammate can also be used on its own in ASI:One.

## The ValiDate team

| Agent | Job | Address |
| --- | --- | --- |
| ValiDate | Talks to the founder in ASI:One, plans the steps, merges the answers | `agent1q04gnfnfl0sl0qusvte6rd0gnzhvtvhzpjceugx9p07wuny8lswlvj0g4mn` |
| ValiDate Intake | Turns what the founder sent into a clean transcript | `agent1q0exnynml2849c0kmafyth4mem8xgs9fzx5yqmyzep8uc7za7lmyssrqeqq` |
| ValiDate Signal Analyst | Labels each sentence, scores the interview, picks the verdict | `agent1q08gppxzdjsvrczrmref9gmd96lpawgdwhx6vpdv6vqc688j72rgutk3qar` |
| ValiDate Strategist | Writes the summary and next steps | `agent1qve9d7cjnn60y8v9ajt5gdz27z0zwvv880q4a04ge3jg4yx2p55hw7hpkqc` |

## Good for

Customer discovery interviews, user interviews, demo calls, startup idea validation, founders and accelerators checking whether there is real market need.

## What it does not do

It measures evidence of demand in what was said. It does not judge whether anyone is being honest.
