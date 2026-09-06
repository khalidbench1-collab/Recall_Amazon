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

### D7 — The grading tool answers immediately and grades in the background
*Added 6 September 2026, forced by the stage 1 spike.*

Alexa+ imposes a round-trip budget of **under 500 ms** on a tool call. A Bedrock call
takes seconds. D3 says grading is ours and server-side; the budget says a tool call
cannot wait for it. Both hold, so the call is split:

- `submit_answer` records the transcript, returns in single-digit milliseconds, and
  starts grading in the background.
- `get_grade` returns the verdict once it exists, and an honest "still thinking" if not.

This is worse for the caller than one blocking tool and it is the only shape that fits.
It also happens to be the right shape for speech: an assistant that says "let me think"
and then answers is normal conversation, whereas four seconds of silence is a failure.

The alternative — grading with a small fast model to fit inside 500 ms — was rejected.
It trades the quality of the one thing that differentiates this project for conformance
to a budget that a two-call split satisfies anyway.

**Consequence:** the scheduler is unaffected (D5 keeps it pure), but the store gains a
pending-grade state, and D6's "no answer given" path now has a sibling: "answer
recorded, grade unavailable". Both must leave the schedule untouched.

### D8 — OAuth 2.1 + PKCE is deferred to the Alexa+ connection, not built into the core
The MCP Toolkit requires OAuth 2.1 authorization code flow with PKCE (S256), and
explicitly does **not** support Dynamic Client Registration, OpenID Connect, or Client
ID Metadata Documents. It also requires a public URL and a Protected Resource Metadata
document at `/.well-known/oauth-authorization-server`.

None of that is needed for MCP Inspector, Claude Code, or the browser harness — the
three clients that actually exercise the code during the build. Auth is therefore a
deployment concern layered on at stage 7, not a core dependency. Building it earlier
would slow every stage in between for no verification benefit.

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

**Substantially reduced on 6 September**, on reading the full rules. The judging
criteria publish worked examples of obvious versus creative per track, and for Alexa+
*creative* explicitly includes "context-aware add-on that maintains state across
sessions". That is a description of a spaced-repetition server rather than a category
it happens to fall into — the state held between sessions is the product. The framing
in the write-up should borrow the judges' words.

The field is also larger than the strategy doc assumed: **2,479 entrants**, not 1,263.

**A new risk in its place, and it lands on the mini challenge.** The same section
defines *obvious* AWS Builder work as "a single Bedrock call for text generation",
which is exactly what `grader.py` is designed to be. The Alexa+ track prize is
unaffected; the $5,000 AWS Builder prize is not. The rules offer two independent exits
— Kiro Crew qualifies on its own with no runtime AWS service, or a second AWS service
with real work to do — and this must be decided by stage 4, not in October.

Second risk: Bedrock grading is non-deterministic, and the demo is recorded. Mitigated
by a seeded demo deck and a calibration fixture set that pins expected score bands.

## Open questions

- ~~Does Amazon offer a way to connect a self-hosted MCP server to a real Alexa+
  account during Preview?~~ **Resolved 6 Sep.** Yes — the Alexa+ MCP Toolkit, via the
  `alexa-ai` CLI and an add-on. Whether Preview enrolment gates it is still unstated in
  the docs; the browser harness makes that immaterial.
- ~~Exact Bedrock model id and region availability.~~ **Resolved 6 Sep.**
  `us.anthropic.claude-sonnet-5` (US geo inference profile) is correct. The bare
  `anthropic.claude-sonnet-5` is unavailable In-Region across every US region, so the
  profile prefix is mandatory rather than optional.
- **New:** does the 500 ms budget apply to the whole tool call or only to the transport
  acknowledgement? D7 is safe under either reading, so this is a question for the
  product feedback write-up, not a blocker.
- **New, and the only live blocker:** no AWS credentials are configured on this
  machine, so the live Bedrock call in `spike/check_bedrock.py` has not been run. Needed
  before stage 4.

## Next step

Implementation plan via the writing-plans skill. Scheduler first, TDD, since it is the
component where correctness is both most important and cheapest to verify.
