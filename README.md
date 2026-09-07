# Recall

**Voice-native spaced repetition, exposed to Alexa+ as a self-hosted MCP server.**

Recall quizzes you out loud while your hands are busy — cooking, driving, folding
laundry — and grades what you actually said for *meaning*, not for exact wording.

> Built for the [Build, Ship, Shape: Amazon Developer Hackathon](https://amazonappdev2026.devpost.com/).
> Primary track: **Alexa+**. Mini challenges: **AWS Builder**, **Open Source**.

---

## Why this exists

Spaced repetition works. Flashcard apps mostly don't get used, because reviewing
requires sitting down with a screen — competing for the exact time of day you have
least of.

Recall moves the review into time you already waste. You answer aloud, which is also
the *better* form of practice: free recall beats visual recognition, and speaking an
answer forces you to produce it rather than recognise it.

### The idea underneath

SM-2, the classic spaced-repetition algorithm, has always taken a **0–5 quality
score** for each review. Every flashcard app in existence collects that score by
making you tap *Again / Hard / Good / Easy* — a self-assessment made *after* you have
already seen the correct answer, which is precisely when people are worst at judging
themselves.

Recall fills that slot honestly. You answer aloud before seeing anything, and a
semantic grader scores the answer from outside. The algorithm has had a slot for this
signal for thirty years; no interface could fill it until voice and language models
arrived together.

---

## How it works

```
  You (speaking)
        |
   Alexa+  ──────  MCP (Streamable HTTP, spec 2025-11-25+)
                          |
                   Recall MCP server  (FastMCP, Python)
                       |         |
                  SQLite      Amazon Bedrock
                  store       semantic grader
                       |
                  SM-2 scheduler (pure functions)
```

Full detail in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).
Design rationale and the decisions behind it in
[`docs/superpowers/specs/2026-09-04-recall-design.md`](docs/superpowers/specs/2026-09-04-recall-design.md).

### Tool surface

| Tool | What it does |
|---|---|
| `add_card` | Creates a card from spoken input |
| `next_due_card` | The single most overdue card, phrased as a question - never a list, never with the answer |
| `submit_answer` | Records what you said and returns immediately. Grading runs behind it. |
| `get_grade` | The verdict, once it exists - or an honest "still thinking" |
| `get_streak_summary` | Current streak and how many cards are due |

**Why five tools and not four.** Alexa+ allows a tool call roughly **500 ms**, and the
fastest Bedrock model measured takes **557 ms** - every model is over budget before the
prompt is even real. So grading is split: `submit_answer` acknowledges in **~18 ms** and
grades in the background, `get_grade` collects the result. It is also better
conversation than blocking would have been. "Let me think", then an answer, is how
people talk; four seconds of silence is a fault.

---

## Running it

```bash
git clone https://github.com/khalidbench1-collab/Recall_Amazon.git
cd Recall_Amazon
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

pytest                             # 77 tests, no credentials needed
python scripts/seed_demo.py        # load 8 cards to try
python -m recall.server            # MCP over Streamable HTTP on :8080
```

### It runs without an AWS account

Grading needs Bedrock; **nothing else does.** With no credentials the server still
starts, serves all five tools, stores and schedules cards, and prints a notice saying
what is missing. Answers come back ungraded - and an ungraded answer never changes a
card's schedule, so running this way corrupts nothing.

To enable grading, create a Bedrock API key (Bedrock console, Discover, API keys):

```bash
cp .env.example .env               # then set AWS_BEARER_TOKEN_BEDROCK
```

### Testing it without an Alexa device

You do not need one. The server is an ordinary web service speaking an open protocol,
so any MCP client drives it:

1. **Unit tests** - scheduler, store, grader and speech shaping: `pytest`
2. **Grader calibration** against the live model, which is the evidence that the
   scoring is fair rather than merely present:
   `RECALL_CALIBRATION=1 pytest tests/test_calibration.py`
   Results in [`docs/CALIBRATION.md`](docs/CALIBRATION.md).
3. **Protocol** - point MCP Inspector or Claude Code at `http://localhost:8080/mcp`
   (no trailing slash; a trailing slash costs a 307 redirect on every call)
4. **Voice** - the browser harness in `sim/` uses the Web Speech API to speak to the
   same server, which is also the hackathon's sanctioned simulated-experience path

---

## Hackathon artefacts

| Document | Purpose |
|---|---|
| [`progress.html`](progress.html) | Stage-by-stage build tracker — open it in a browser |
| [`submission.html`](submission.html) | Every Devpost field, paste-ready — open it in a browser |
| [`docs/DEMO-SCRIPT.md`](docs/DEMO-SCRIPT.md) | Demo video script, timed to the second |
| [`docs/FRICTION-LOG.md`](docs/FRICTION-LOG.md) | Live friction log (worth up to a 10% judging bonus) |
| [`docs/PRODUCT-FEEDBACK.md`](docs/PRODUCT-FEEDBACK.md) | Required per-SDK product feedback, written as we go |
| [`docs/CALIBRATION.md`](docs/CALIBRATION.md) | Grader calibration against the live model - generated, not written |
| [`Assets/hackathon-strategy.html`](Assets/hackathon-strategy.html) | The strategy analysis this project came out of |

## Licence

MIT — see [`LICENSE`](LICENSE).
