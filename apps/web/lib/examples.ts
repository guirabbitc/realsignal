// Made-up interviews for "Try an example", written for valiDate's users: early-stage founders building
// tech products, interviewing the founders and tech leads they sell to. Each example runs under its own
// example idea (EXAMPLE_IDEAS) so its verdict does not depend on whatever idea the founder is on.
// They are not the analyzer's reference fixtures: services/analyzer/fixtures/ stays the human-owned
// reference for tests and the journey.

export type ExampleType = "real_pain" | "mixed" | "polite" | "wrong_problem" | "too_short" | "demo";

export const EXAMPLE_TYPES: { type: ExampleType; label: string; description: string }[] = [
  { type: "real_pain", label: "Real pain", description: "They say what the problem cost them and commit to a next step." },
  { type: "mixed", label: "Mixed signals", description: "Some real pain, a lot of maybes." },
  { type: "polite", label: "Just polite", description: "Compliments and maybes, nothing concrete." },
  { type: "wrong_problem", label: "Wrong problem", description: "Real pain, but not the one the idea solves." },
  { type: "too_short", label: "Too short", description: "Too little said to judge either way." },
  { type: "demo", label: "Demo call", description: "Reactions to a product demo, not a discovery interview." },
];

export const EXAMPLE_IDEAS = {
  investor_updates: "Automated monthly investor updates from Stripe, HubSpot and bank data for seed-stage founders.",
  security_review: "An AI code reviewer that flags security bugs in pull requests for startups without a security engineer.",
  support_bugs: "A tool that turns customer support tickets into a ranked bug list for early-stage SaaS teams.",
  fractional_cfo: "A marketplace that matches seed-stage startups with vetted fractional CFOs.",
} as const;

export type ExampleIdeaKey = keyof typeof EXAMPLE_IDEAS;

export interface Example {
  key: string;
  type: ExampleType;
  kind: "interview" | "demo";
  idea: ExampleIdeaKey;
  intervieweeLabel: string;
  /** Our one-line summary for the card; not a quote from the transcript. */
  hook: string;
  transcript: string;
}

export const EXAMPLES: Example[] = [
  {
    key: "investor-real-pain",
    type: "real_pain",
    kind: "interview",
    idea: "investor_updates",
    intervieweeLabel: "Sam, CEO of a 10-person B2B SaaS",
    hook: "Six hours a month, a late update to his lead investor, and a paid analyst who quit.",
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
  {
    key: "investor-mixed",
    type: "mixed",
    kind: "interview",
    idea: "investor_updates",
    intervieweeLabel: "Marco, solo founder of a dev tools startup",
    hook: "One embarrassing MRR mistake a quarter, but most months the update is fine.",
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
    key: "investor-polite",
    type: "polite",
    kind: "interview",
    idea: "investor_updates",
    intervieweeLabel: "Priya, co-founder of a pre-seed AI startup",
    hook: "Loves the idea and would maybe pay, but has six angels and no real problem.",
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
    key: "security-real-pain",
    type: "real_pain",
    kind: "interview",
    idea: "security_review",
    intervieweeLabel: "Lena, CTO of a 6-engineer fintech",
    hook: "Leaked a Stripe key, paid $12,000 for a pentest, and wants to install it tomorrow.",
    transcript: `Founder: Thanks for jumping on. How do you review code for security today?
Customer: Honestly, we don't, not properly. Two of us review every pull request, but we look at logic, not security. In May a junior engineer committed a Stripe secret key to a public repo and it sat there for nine days.
Founder: What happened after that?
Customer: We rotated every key, lost a whole weekend, and our bank partner made us pay for an external pentest. That cost 12,000 dollars and it found four more issues we had already shipped without noticing.
Founder: What have you tried since then?
Customer: We turned on GitHub secret scanning and tried Snyk for a month. Snyk flagged hundreds of dependency warnings, nobody read them, and we turned it off. I also spend about three hours a week re-reading risky pull requests myself.
Founder: What would a tool need to do for you to rely on it?
Customer: Comment on the pull request itself, only when something is actually exploitable, and explain the fix in one paragraph. If it had caught the key leak, it would have paid for itself for years.
Founder: Would you try an early version?
Customer: Yes. Send me the install link and I'll add it to our main repo tomorrow morning. Our SOC 2 audit starts in November, so I can give you a lot of real pull requests to test against.
`,
  },
  {
    key: "security-wrong-problem",
    type: "wrong_problem",
    kind: "interview",
    idea: "security_review",
    intervieweeLabel: "Tomás, CTO of a 15-person healthtech",
    hook: "Security is already covered; flaky CI tests cost his team $900 a month.",
    transcript: `Founder: How do you handle security in code review today?
Customer: We're in healthcare, so it's covered. We pay a security firm to review every release, and HIPAA made us set that up last year. Honestly, security review is not a problem for us at all.
Founder: When did code review last slow you down?
Customer: Every single day, but never because of security. Our test suite takes forty minutes and about one run in five fails for no reason. Last Thursday a hotfix sat for three hours because CI kept failing on a flaky test.
Founder: What have you tried?
Customer: We split the suite and bought bigger runners, which now costs us 900 dollars a month. One engineer spends most Fridays hunting flaky tests, and it still breaks.
Founder: Would an AI reviewer that flags security bugs help your team?
Customer: No, I don't think we'd use it. Security is the one part of review that already works for us, and I wouldn't pay for a second opinion on it.
Founder: What would you pay for, then?
Customer: Something that finds and quarantines flaky tests automatically. Same approach as yours, an AI reading our pull requests and CI runs, just pointed at test failures instead of security. If you built that, I'd put it on a card this week.
`,
  },
  {
    key: "security-demo",
    type: "demo",
    kind: "demo",
    idea: "security_review",
    intervieweeLabel: "Grace, VP of Engineering at a Series A startup",
    hook: "Likes the demo, got burned by noisy tools, and wants a silent trial first.",
    transcript: `Founder: That's the demo: it read the pull request, flagged the SQL injection on line 42 and suggested the fix. What did you think?
Customer: That's slick, honestly. The comment points at the exact line, and it's much shorter than what our current scanner writes.
Founder: How does that compare to how your team works today?
Customer: Today we run Semgrep in CI and a senior engineer reviews anything that touches auth. Last quarter we still shipped an access-control bug that a customer reported, and it took us two days to patch and explain.
Founder: What would you need to see before using it on your real repos?
Customer: Proof that it doesn't drown us in noise. We turned off two tools last year because of false positives. I'd want to run it in silent mode for two weeks and compare it with our Semgrep results.
Founder: Who else would be involved in that decision?
Customer: Our security lead and our CTO. Budget isn't the problem, trust is. If the silent run looks good, we have money set aside for tooling this quarter.
Founder: Can we set up that silent run?
Customer: Maybe, let me talk to our security lead first. Send me the docs on what data you store and how long you keep it, and I'll get back to you next week.
`,
  },
  {
    key: "support-mixed",
    type: "mixed",
    kind: "interview",
    idea: "support_bugs",
    intervieweeLabel: "Hannah, head of product at a 25-person SaaS",
    hook: "A billing bug slipped through last month, but that happens twice a year.",
    transcript: `Founder: How do bugs from support tickets reach your engineers today?
Customer: Our two support people tag tickets in Intercom, and on Mondays I skim the tagged ones and create Linear issues. It's a bit tedious, but it works.
Founder: When did a customer bug last slip through?
Customer: Last month a billing bug was reported by a handful of customers before anyone connected the tickets. We sorted it out in about two weeks, and a few people got refunds.
Founder: How often does something like that happen?
Customer: Maybe twice a year, honestly, it's not every month. Most weeks the Monday routine catches things in time and it's fine.
Founder: What have you done about it so far?
Customer: Nothing really, I keep a saved view in Intercom and check it when I remember. Before a big release I spend an afternoon reading old tickets.
Founder: If a tool grouped tickets into bugs and ranked them, how would that fit?
Customer: I think that sounds interesting, I'd probably try it. It would be nice to stop reading every ticket myself. But I'm not sure our engineers would trust an automatic ranking.
Founder: What would make it worth paying for?
Customer: If it caught the next billing bug faster, maybe. I'd have to see it working first. It's a nice idea though, I can see why you're excited about it.
`,
  },
  {
    key: "support-too-short",
    type: "too_short",
    kind: "interview",
    idea: "support_bugs",
    intervieweeLabel: "Dev, founder of a 3-person SaaS",
    hook: "Four short answers between meetings. Not enough to judge yet.",
    transcript: `Founder: How do you track bugs that customers report?
Customer: In Linear, mostly.
Founder: How is that going?
Customer: Fine, I guess.
Founder: Would a tool that turns tickets into a bug list help?
Customer: Sounds cool.
Founder: Can I follow up next week?
Customer: Sure, ping me.
`,
  },
  {
    key: "cfo-real-pain",
    type: "real_pain",
    kind: "interview",
    idea: "fractional_cfo",
    intervieweeLabel: "Aisha, CEO of a seed-stage climate tech startup",
    hook: "A model error delayed her round by five weeks, and a $6,000 CFO disappeared.",
    transcript: `Founder: How do you handle finance today, beyond bookkeeping?
Customer: Badly. Our bookkeeper closes the month, but nobody owns the model. Before our seed extension I rebuilt the financial model myself over two weekends, and an investor still found a formula error in the runway tab.
Founder: What did that cost you?
Customer: The round slipped by five weeks while we fixed the model and re-ran diligence. We had to cut a contractor to stretch our cash, and I lost about forty hours I should have spent with customers.
Founder: What have you tried?
Customer: We hired a fractional CFO through a friend last year. He was good, but he disappeared after two months when he took a full-time job. We had paid him 6,000 dollars and had to start over. I also talked to two CFO agencies, and both wanted a twelve-month contract.
Founder: What would have to be true for you to use a marketplace for this?
Customer: The CFO has to have worked with climate or hardware startups, start within a week, and work month to month. If that existed, I'd sign up before our Series A prep in January.
Founder: Want to try it with a real match?
Customer: Yes. Send me two profiles this week and I'll book calls with both. If one fits, we'll start in November, and I'll introduce you to two other founders in our cohort with the same problem.
`,
  },
  {
    key: "cfo-polite",
    type: "polite",
    kind: "interview",
    idea: "fractional_cfo",
    intervieweeLabel: "Jordan, co-founder of a consumer app startup",
    hook: "Thinks every founder would want one; their accountant is fine for now.",
    transcript: `Founder: So we're building a marketplace where seed-stage founders can find a vetted fractional CFO in a day. Great idea, right?
Customer: Oh, that sounds great. Finance is such a pain for founders, I really love that someone is finally working on it.
Founder: Wouldn't it be amazing to have a CFO on call whenever you need one?
Customer: Yeah, totally, that would be amazing. I think every founder would want that kind of support, especially first-time founders like us.
Founder: Would you use it?
Customer: Sure, I'd probably use something like that when we raise our next round, or whenever things get more complicated. Maybe sooner, if it's not too expensive and the CFOs are good.
Founder: Would you pay 1,500 dollars a month for a fractional CFO?
Customer: Maybe, it depends. I would need to think about it, but it could make sense once we have more revenue coming in.
Founder: Anything you'd want to see in it?
Customer: Not really, it sounds really well thought out already. You obviously know what founders need. I'm sure it will take off, honestly.
Founder: Thanks, that means a lot.
Customer: Of course, happy to help. Our accountant handles the basics today, so we're fine for now, but I'll definitely keep you in mind. Send me something when it launches, I'd love to take a look.
`,
  },
];

/** Shown on the upload page; the rest are on /examples. */
export const FEATURED_EXAMPLE_KEYS = ["investor-real-pain", "investor-mixed", "investor-polite"];

const EXAMPLE_IDEA_TEXTS = new Set<string>(Object.values(EXAMPLE_IDEAS));

export function isExampleIdea(oneLiner: string): boolean {
  return EXAMPLE_IDEA_TEXTS.has(oneLiner);
}
