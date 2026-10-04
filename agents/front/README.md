# valiDate

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

valiDate is an AI coach for customer interviews. It reads the transcript of a discovery interview and tells a founder how much real interest is in it.

Customers are polite. "Cool idea, I'd use that" feels like validation, but it is not evidence. valiDate separates what the customer actually did, paid for or committed to from compliments and hypotheticals.

## What you get

- A verdict: keep going, narrow down, try a new angle, pivot, or not enough evidence yet
- A signal score from 0 to 100
- The reasons, and the strongest quotes behind them, word for word
- Your own interviewing mistakes: talking too much, pitching early, leading questions
- The next 3 questions to ask

## How to use it

1. Say hi. valiDate asks what idea you are testing; answer in one sentence.
2. Paste the interview transcript, with every turn starting with the speaker's name and a colon.

You can send more interviews for the same idea, or write `new idea: ...` to test another one.

**Example**

> WhatsApp bot that takes restaurant reservations

> Founder: How do you handle bookings today?
> Customer: I pay someone 300 dollars a month just to reply to booking messages.
> Customer: Send me the pilot link and I'll set it up on Monday.

## Free and paid

The verdict, the score, the reasons and the next questions are free. The sentence-by-sentence breakdown, every customer sentence with its category and how likely it is a real signal, is a paid extra: valiDate shows the price, sends a payment request (Agent Payment Protocol, FET on the Fetch testnet), checks the transfer on the ledger, and then delivers it.

In ASI:One the verdict comes with a card: buttons for the breakdown, another interview, or a new idea.

## How it works

valiDate is a team of four agents. This one plans the work and talks to you. It hands the interview to Intake, then to the Signal Analyst, then to the Strategist, and merges their answers into one reply. If a teammate does not answer, it runs the same analysis itself. Each teammate can also be used on its own in ASI:One.

A calibrated decision model (Jev) makes every judgment, a separate model writes the text, and the score is plain arithmetic.

## The valiDate team

| Agent | Job | Address |
| --- | --- | --- |
| valiDate | Talks to the founder, plans the steps, merges the answers | `agent1q04gnfnfl0sl0qusvte6rd0gnzhvtvhzpjceugx9p07wuny8lswlvj0g4mn` |
| valiDate Intake | Works out who is the interviewer and who is the customer | `agent1q0exnynml2849c0kmafyth4mem8xgs9fzx5yqmyzep8uc7za7lmyssrqeqq` |
| valiDate Signal Analyst | Judges each customer sentence, scores the interview, picks the verdict | `agent1q08gppxzdjsvrczrmref9gmd96lpawgdwhx6vpdv6vqc688j72rgutk3qar` |
| valiDate Strategist | Writes the read-out and the next questions | `agent1qve9d7cjnn60y8v9ajt5gdz27z0zwvv880q4a04ge3jg4yx2p55hw7hpkqc` |

## What it does not do

It judges statements about a product, never the person. It does not judge whether anyone is being honest.
