// Made-up interviews for the "Try an example" buttons, written for valiDate's users: early-stage
// founders building tech products. All three test the same idea (EXAMPLE_IDEA) with other founders.
// They mirror the shape of the analyzer's reference fixtures (polite < mixed < real_pain) but are not
// them: services/analyzer/fixtures/ stays the human-owned reference for tests and the journey.

export type ExampleKey = "polite" | "mixed" | "real_pain";

export interface Example {
  key: ExampleKey;
  title: string;
  intervieweeLabel: string;
  transcript: string;
}

export const EXAMPLE_IDEA = "Automated monthly investor updates from Stripe, HubSpot and bank data for seed-stage founders.";

export const EXAMPLES: Example[] = [
  {
    key: "polite",
    title: "Polite interview",
    intervieweeLabel: "Priya, co-founder of a pre-seed AI startup",
    transcript: `Founder: So we're building an AI tool that writes your monthly investor update automatically from Stripe, HubSpot and your bank account. Pretty cool, right?
Customer: Oh, that sounds really cool. I love anything that uses AI like that, honestly, every founder I know would want it.
Founder: Don't you think founders would save a lot of time with something like this?
Customer: Yeah, definitely, I think a lot of founders would find it useful. Investor updates are one of those things everyone talks about.
Founder: Would you use it if it existed?
Customer: Sure, I'd probably try something like that at some point. I would maybe use it if the setup is quick and it connects to everything.
Founder: And would you pay for it, like 49 dollars a month?
Customer: Maybe, it depends. I would have to think about it, but it could be worth it for founders with a lot of investors.
Founder: Great. Anything else you'd want in it?
Customer: Not really, it sounds great already. You clearly know the space, I'm sure it will do well. Good luck with it, really, I mean it.
Founder: Thanks so much, this is super encouraging.
Customer: Of course, happy to help. We only have six angels, so updates are not a big deal for us yet, but I'm sure bigger cap tables would love it. Keep me posted, I'd love to see what you build.
`,
  },
  {
    key: "mixed",
    title: "Mixed interview",
    intervieweeLabel: "Marco, solo founder of a dev tools startup",
    transcript: `Founder: How do you send updates to your investors today?
Customer: Mostly a monthly email, sometimes a short Loom. We have about eight angels and one seed fund.
Founder: When did an update last go wrong?
Customer: Two months ago the MRR in my update didn't match Stripe because I pulled the number before refunds cleared. The fund partner caught it on a call, which was embarrassing.
Founder: How often does that happen?
Customer: Maybe once a quarter, honestly, it's not every month. Most months the email takes me an hour or two and it's fine.
Founder: What have you done about it so far?
Customer: Nothing really, I keep a spreadsheet template and copy last month's update. Before board meetings I spend about a day checking every number with our accountant.
Founder: If a tool drafted the update from your Stripe and bank data, how would that fit?
Customer: I think that sounds interesting, I'd probably try it. It would be nice to stop copying numbers by hand. But I'm not sure I'd trust it with the commentary, my investors like hearing it in my own words.
Founder: What would make it worth paying for?
Customer: If it stopped the wrong numbers, maybe. I'd have to see it working first. It's a nice idea though, I can see why you're excited about it.
`,
  },
  {
    key: "real_pain",
    title: "Real pain interview",
    intervieweeLabel: "Sam, CEO of a 10-person B2B SaaS",
    transcript: `Founder: Thanks for making time. How do you put together your investor update today?
Customer: Honestly it's painful. Every month I export revenue from Stripe, pipeline from HubSpot and cash from our bank, paste it all into a Google Doc and write the commentary myself. Last month it took me most of a Sunday.
Founder: What did that cost you?
Customer: About six hours of my time every month. In March I sent the update eleven days late, and two investors emailed to ask if something was wrong, including the one leading our next round.
Founder: Have you tried anything else to fix it?
Customer: We tried Visible last year. We cancelled after three months because I still typed every number by hand. Then I paid a freelance analyst 400 dollars a month to prepare the numbers, but she left in June.
Founder: What would have to be true for you to switch to something new?
Customer: It has to pull straight from Stripe, HubSpot and Mercury without me touching a spreadsheet. If the numbers are right and I only edit the commentary, I would pay what I paid the analyst.
Founder: Would you be open to trying an early version?
Customer: Yes. Send me the pilot link and I'll connect our accounts on Monday so it can draft the October update. You can also talk to my co-founder Ana, she owns our metrics, I'll introduce you by email today.
`,
  },
];
