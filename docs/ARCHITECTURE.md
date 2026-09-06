# Architecture

## System boundary

Recall is a **self-hosted MCP server**. Alexa+ is a client, not a component. That
boundary is the reason this project needs no hardware: the protocol is
client-agnostic, so any MCP client — Alexa+, MCP Inspector, Claude Code, or the
browser harness in `sim/` — exercises the same code path.

```
   speech in                                   speech out
       |                                            ^
       v                                            |
  +----------------------------------------------------+
  |                    Alexa+  (client)                 |
  +----------------------------------------------------+
                          |
             MCP over Streamable HTTP (spec 2025-11-25+)
                          |
  +----------------------------------------------------+
  |              recall.server   (FastMCP)              |
  |   tool registration, request validation, framing    |
  +----------------------------------------------------+
        |                  |                    |
        v                  v                    v
  +-----------+     +--------------+     +---------------+
  | store.py  |     | scheduler.py |     |  grader.py    |
  | SQLite    |     | SM-2, pure   |     |  Bedrock      |
  +-----------+     +--------------+     +---------------+
```

## Components

### `server.py` — the MCP surface
Registers four tools, validates input, and shapes every response for *speech*. No
business logic lives here. Its single responsibility is translating between the MCP
wire format and the domain modules.

**Speech-shaping is a real constraint, not a formatting detail.** A response that
reads fine as JSON can be unbearable read aloud. Responses are capped in length, avoid
enumerated lists longer than three items, and never contain markup.

### `store.py` — persistence
SQLite, one file, accessed through a thin repository layer. Two tables: `cards`
(prompt, answer, scheduling state) and `reviews` (an append-only log of every graded
attempt). The review log is kept separate from card state deliberately — it is what
makes `get_streak_summary` possible and what lets grader calibration be evaluated
retrospectively against real attempts.

### `scheduler.py` — SM-2
Pure functions. No I/O, no clock access (the current time is passed in). Takes a card's
current interval, repetition count and ease factor plus a 0–5 quality score, and
returns the next interval and ease factor.

Purity here is a deliberate testing decision: the scheduling rules are the part most
likely to be subtly wrong, and pure functions let the entire algorithm be tested
exhaustively without a database or a fixed clock.

### `grader.py` — semantic grading via Bedrock
Takes the expected answer and the transcribed spoken answer, returns a 0–5 quality
score plus one short spoken sentence explaining the score.

This runs **server-side**, which is the project's central architectural decision. The
alternative — letting the calling model grade — would reduce this server to a card
database, put the interesting behaviour outside the repo, and forfeit the AWS Builder
mini challenge. Server-side grading means the scoring logic, its prompt, and its
calibration are all ours and all testable.

## Data flow: one review

1. Alexa+ calls `list_due_cards`. Store returns cards where `due_at <= now`, oldest
   debt first.
2. Alexa+ speaks a prompt. The user answers aloud; Alexa+ transcribes.
3. Alexa+ calls `submit_answer` with the card id and the transcript. It records the
   attempt, kicks off grading, and returns immediately — see decision D7. Alexa+ has a
   round-trip budget of under 500 ms, which a model call cannot meet.
4. In the background, `grader.py` asks Bedrock for a 0–5 score and a one-line
   explanation.
5. `scheduler.py` computes the next interval from that score.
6. `store.py` writes the new card state and appends to the review log.
7. Alexa+ calls `get_grade`, which returns the explanation shaped for speech — or an
   honest "still thinking" if grading has not landed yet.

## Error handling

Three failure classes, handled differently:

- **Bedrock unavailable or slow.** Grading is the only network dependency. Slowness is
  now expected rather than exceptional, which is why it is handled by the two-call split
  above rather than by a timeout. On outright failure
  the tool returns a graded-as-unknown result that leaves the card's schedule
  untouched rather than corrupting it with a guess, and says so aloud. A silently
  mis-scheduled card is worse than a skipped review.
- **Ambiguous or empty transcript.** Treated as "no answer given", not as a wrong
  answer — a speech recognition failure is not a memory failure and must not be
  allowed to damage the user's scheduling data.
- **Store errors.** Fail loudly. Data loss is unacceptable and a spoken error is
  better than a silent one.

## Testing strategy

| Layer | Question it answers | Tooling |
|---|---|---|
| Unit | Does SM-2 do the right thing? | `pytest`, pure functions |
| Calibration | Does the grader score fairly? | Fixture set of answer pairs with expected score bands |
| Protocol | Is this a valid MCP server? | MCP Inspector, Claude Code as client |
| Voice | Does it work *spoken*? | Browser harness in `sim/`, Web Speech API |

The calibration layer matters most. It is the evidence that grading is ours rather
than the platform's, and it is what makes the demo reproducible on video.
