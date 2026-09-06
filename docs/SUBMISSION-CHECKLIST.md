# Submission checklist

Devpost submission forms have more required fields than anyone expects. Never submit
on deadline day.

**Deadline: 23 October 2026, 21:00 GMT+2** (12:00 PT).
**Judging: 9–20 November. Winners: 3 December.**

## Do these first — they gate everything else

- [ ] **Register on Devpost.** The hackathon page still shows a "Join hackathon"
      button, which means registration may not have happened. Nothing below is
      possible without it.
- [ ] **Request the $150 AWS promotional credits** at
      https://forms.gle/5hyhr1u6x3fuV2aW7 — open to registered entrants only, closes
      21 October 12:00 PT, and awarded *while supplies last*. At roughly $0.002 per
      graded card this covers about 75,000 reviews, so it removes the running cost of
      the project entirely. Apply early: a queue against 2,479 entrants is not a
      thing to join in the last week, and credits that arrive after the build is
      finished are worth nothing.
- [ ] **Create the AWS account and enable Bedrock model access** for
      `us.anthropic.claude-sonnet-5`. This is the stage 1 blocker and is on the
      critical path to stage 4.

## Keep it alive after submitting

Submission closes 23 October but judging runs to **20 November**. The rules require
the project to remain available, free of charge and unrestricted, for testing until
the judging period ends.

- [ ] Repo stays public and unchanged through 20 November
- [ ] The server still runs from a clean clone in late November — which means it must
      start and serve all four tools **without AWS credentials**, degrading to an
      honest "grading unavailable" rather than crashing. A judge testing on 19
      November will not have our Bedrock access.
- [ ] If anything is hosted privately, testing credentials are in the submission

## Hard requirements

- [ ] Public GitHub repo containing all source, assets and run instructions
- [ ] Open-source licence **visible in the repo's About section**, not just as a file
- [ ] Repo demonstrably calls the track technology in code — a real import, entry
      point or loaded MCP config. A README mention does not qualify.
- [ ] MCP server conforms to spec 2025-11-25 or later, over Streamable HTTP
- [ ] Demo video under 3 minutes, public, in English, on YouTube or Vimeo
- [ ] No third-party trademarks or licensed music in the video
- [ ] Text description of what it does and how it works
- [ ] Product feedback on every tool, API and SDK used (`docs/PRODUCT-FEEDBACK.md`)
- [ ] Tracks and mini challenges declared: Alexa+ / AWS Builder / Open Source

## Mini challenge extras

- [ ] **AWS Builder** — AWS services described in the feedback answer with documented
      integration.
      **Warning, from the published judging language:** *obvious* is defined as "a
      single Bedrock call for text generation" — which is precisely what `grader.py`
      is today. *Creative* is "multi-service pipeline (Bedrock + AgentCore + Strands),
      agentic architecture." Two routes out, and the rules confirm either is enough on
      its own: build with **Kiro Crew** (which qualifies without any runtime AWS
      service at all), or add a second AWS service with a real job to do. Decide by
      stage 4; do not discover this in October.
- [ ] **Open Source** — contribution URL, repo URL, GitHub username, and a short
      description of what was done, how it works, and why it matters.
      Judged the same way: *obvious* is "README update, typo fix, minor formatting";
      *creative* is "meaningful feature addition with tests". The PR must carry tests.

## Scoring bonuses

- [ ] Friction log entries with severity, workaround and actionable suggestion
      (`docs/FRICTION-LOG.md`) — up to a 10% bonus
- [ ] Feature requests with urgency ratings — optional

## What the judges call creative, in our track

Quoted from the rules, because it is the clearest steer available and most entrants
will not read this far:

> **Alexa+** — *Obvious:* single-turn Q&A bot, basic MCP wrapper around an existing
> API. *Creative:* agentic workflow that orchestrates across services autonomously,
> **context-aware add-on that maintains state across sessions**, purchasing
> capabilities, media support (cards, carousels, etc), MCP Apps, Agent Skills.

The bolded phrase describes a spaced-repetition server exactly — the state held
between sessions *is* the product, not a feature of it. This is the strongest
available answer to the "isn't this just flashcards" risk in the design spec, and the
demo and write-up should both use the judges' own framing rather than ours.

Cheap win also visible in that list: **media support (cards, carousels)**. Alexa+
devices have screens, and a review session has an obvious visual companion.

## Video discipline

- [ ] Strongest 30 seconds first; judges are not required to watch past 3 minutes
- [ ] The simulated harness is **labelled as simulated** — the rules permit it, and
      implying real device footage is a disqualification risk
- [ ] Architecture explained second, after the payoff
