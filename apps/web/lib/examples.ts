// Reference transcripts for the "Try an example" buttons. Copied verbatim from
// services/analyzer/fixtures/*.txt (human-owned): change them there, then copy again.
// tests/examples.test.ts fails if this copy drifts from the fixtures.

export type ExampleKey = "polite" | "mixed" | "real_pain";

export interface Example {
  key: ExampleKey;
  title: string;
  intervieweeLabel: string;
  transcript: string;
}

export const EXAMPLES: Example[] = [
  {
    key: "polite",
    title: "Polite interview",
    intervieweeLabel: "Polly, bistro manager",
    transcript: `Founder: So we're building a WhatsApp bot that takes restaurant reservations automatically, with AI, and it syncs with your calendar. Pretty cool, right?
Customer: Oh, that sounds like a really cool app. I love the idea, honestly, it's the kind of thing everyone talks about these days.
Founder: Don't you think restaurants would save a lot of time with something like this?
Customer: Yeah, definitely, I think a lot of places would find it useful. It's very modern, and people like modern things.
Founder: Would you use it if it existed?
Customer: Sure, I'd probably use something like that at some point. I would maybe try it, if it's easy and doesn't take long to set up.
Founder: And would you pay for it, like 50 dollars a month?
Customer: Maybe, it depends. I would have to think about it, but it could be worth it for some restaurants, especially the busy ones downtown.
Founder: Great. Anything else you'd want in it?
Customer: Not really, it sounds great already. You guys are clearly smart, I'm sure it will do well. Good luck with it, really, I mean it.
Founder: Thanks so much, this is super encouraging.
Customer: Of course, happy to help. We have about twelve tables here, so it's a small place, but I'm sure bigger restaurants would love it. Keep me posted on how it goes, I'd love to see what you build.
`,
  },
  {
    key: "mixed",
    title: "Mixed interview",
    intervieweeLabel: "Mia, family restaurant owner",
    transcript: `Founder: How do people book a table with you today?
Customer: Mostly phone calls, some WhatsApp. We have about twelve tables and two seatings a night.
Founder: When did booking last go wrong?
Customer: Two weeks ago we double-booked a table on a Saturday because a WhatsApp message and a phone call came in at the same time. We had to give that couple free desserts and they still left a bad review.
Founder: How often does that happen?
Customer: Maybe once a month, honestly, it's not every week. Most nights the phone works fine for us.
Founder: What have you done about it so far?
Customer: Nothing really, my sister keeps a paper book at the front and we check it when we remember. On Sundays I spend about an hour calling people back to confirm their tables.
Founder: If a WhatsApp bot took the bookings, how would that fit?
Customer: I think that sounds interesting, I'd probably try it. It would be nice for the younger customers who never call. But I'm not sure my older regulars would use it, they like to talk to someone on the phone.
Founder: What would make it worth paying for?
Customer: If it stopped the double bookings, maybe. I'd have to see it working first. It's a nice idea though, I can see why you're excited about it.
`,
  },
  {
    key: "real_pain",
    title: "Real pain interview",
    intervieweeLabel: "Maria, restaurant owner",
    transcript: `Founder: Thanks for making time. How do you handle reservations today?
Customer: Honestly it's a mess. Most of our bookings come in through WhatsApp, and I answer them myself between services. Last Friday I missed three messages and two tables of six walked in to a full room.
Founder: What did that cost you?
Customer: Those two tables were about 900 dollars of revenue we lost in one night. It happens almost every weekend. I pay someone 300 dollars a month just to sit with my phone and reply to booking messages on Friday and Saturday.
Founder: Have you tried anything else to fix it?
Customer: We tried OpenTable last year. We cancelled after four months because our regulars refused to download an app, they just keep texting us on WhatsApp. I also tried a Google Form, and nobody filled it in.
Founder: What would have to be true for you to switch to something new?
Customer: It has to work inside WhatsApp, because that's where my customers already are. If it can confirm a table and put it in my booking sheet, I would pay what I pay my assistant today.
Founder: Would you be open to trying an early version?
Customer: Yes. Send me the pilot link and I'll set it up on Monday for the lunch service. You can also talk to my manager Paulo, he handles the floor plan, I'll introduce you by email today.
`,
  },
];
