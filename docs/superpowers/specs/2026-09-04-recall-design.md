# Recall — design

**Date:** 4 September 2026
**Status:** approved, pre-implementation
**Context:** Build, Ship, Shape: Amazon Developer Hackathon — Alexa+ track, deadline 23 October 2026

---

## Purpose

A spaced-repetition study system exposed as MCP tools, so Alexa+ can drill the user
out loud during time that is otherwise unusable for study, and grade spoken answers
for meaning rather than exact wording.

## Success criteria

1. A judge can clone the repo and have a working MCP server in under five minutes.
2. A 90-second demo shows a card asked aloud, answered imperfectly aloud, graded
   correctly on nuance, and rescheduled.
3. The repo demonstrably *calls* MCP and Bedrock in code — imports and entry points,
   not README claims.
4. The friction log is captured live from day one, not reconstructed at the end.

## Scope

**In:** spoken card capture, spoken review, semantic grading, SM-2 scheduling, streak
and retention summary, a browser voice harness.

**Out (explicitly):** document ingestion, deck sharing, multi-user accounts, a mobile
app, Anki import. Each was considered and cut. Scope discipline is the strategy: the
competitive advantage here is polish and the write-up, and both need the time.

## Decisions

### D1 — Alexa+ track, both mini challenges
Highest prize in the event, no hardware dependency, and the rules provide a simulated
web-app fallback that removes tail risk entirely. Open Source is satisfied by the MIT
licence plus one PR to a public repo. AWS Builder is satisfied by D3.

### D2 — Spoken capture only, no ingestion
Ingestion would be the more impressive engineering, but it moves the centre of gravity
away from the thing that makes this project voice-native. Cutting it buys roughly two
weeks that go into grading quality and the submission write-up.

### D3 — Grading runs server-side via Bedrock
The alternative is letting the calling model grade the answer. That is less code, but
it reduces this server to a card database, puts the interesting behaviour outside the
repo where judges cannot assess it, and forfeits the AWS Builder mini challenge.
Server-side grading makes the scoring prompt and its calibration our artefact.

### D4 — SM-2 rather than FSRS
FSRS is the better algorithm, but SM-2's 0–5 quality input is the exact shape of what
a semantic grader produces, and its simplicity keeps the scheduler small enough to
test exhaustively. The project's claim is about the *input signal*, not the algorithm.

### D5 — The scheduler is pure; the clock is injected
No I/O and no `now()` inside scheduling logic. This is what makes multi-month
scheduling behaviour testable in milliseconds.

### D6 — A speech-recognition failure must never damage scheduling data
An empty or unintelligible transcript is "no answer given", not a wrong answer. The
card's schedule is left untouched. This is stated as a design rule because the
tempting default — treat silence as failure — quietly corrupts the user's data.

## The central insight

SM-2 has always required a 0–5 self-assessment, collected by every existing flashcard
app *after* the user has seen the correct answer — the moment at which self-assessment
is least reliable. A grader scoring a spoken answer produces that signal from outside,
before the answer is revealed. The algorithm has had a slot for this for thirty years;
the interface to fill it did not exist until voice and language models arrived
together.

This is the one-sentence answer to "isn't this just flashcards", and it is the claim
the demo has to make legible in 90 seconds.

## Known risk

Spaced repetition is a crowded idea, including at hackathons. Two of the four judging
criteria (Quality of Idea, Potential Impact) are differentiation scores. The mitigation
is D3 and the insight above: the differentiator must be visibly *ours* in the code and
audible in the demo, not asserted in the README.

Second risk: Bedrock grading is non-deterministic, and the demo is recorded. Mitigated
by a seeded demo deck and a calibration fixture set that pins expected score bands.

## Open questions

- Does Amazon offer a way to connect a self-hosted MCP server to a real Alexa+ account
  during Preview? Day-one spike. Not a blocker — the browser harness covers either
  outcome.
- Exact Bedrock model id and region availability. To confirm against current docs
  before `grader.py` is written.

## Next step

Implementation plan via the writing-plans skill. Scheduler first, TDD, since it is the
component where correctness is both most important and cheapest to verify.
