# Recall

**Voice-native spaced repetition, exposed to Alexa+ as a self-hosted MCP server.**

Recall quizzes you out loud while your hands are busy — cooking, driving, folding
laundry — and grades what you actually said for *meaning*, not for exact wording.

> Built for the [Build, Ship, Shape: Amazon Developer Hackathon](https://amazon-developer.devpost.com/).
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
| `list_due_cards` | Cards scheduled for review now, oldest debt first |
| `grade_response` | Scores a spoken answer 0–5 via Bedrock, reschedules the card |
| `add_card` | Creates a card from spoken input |
| `get_streak_summary` | Review streak and retention over time |

---

## Running it

```bash
git clone <this repo>
cd amazon_app
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cp .env.example .env        # add your AWS region + Bedrock model id
python -m recall.server     # serves MCP over Streamable HTTP on :8080
```

### Testing it without an Alexa device

You do not need one. The server is an ordinary web service speaking an open protocol,
so any MCP client drives it:

1. **Unit tests** — the scheduler and grader calibration, no MCP involved: `pytest`
2. **Protocol** — point MCP Inspector or Claude Code at `http://localhost:8080/mcp`
3. **Voice** — the browser harness in `sim/` uses the Web Speech API to speak to the
   same server, which is also the hackathon's sanctioned simulated-experience path

---

## Hackathon artefacts

| Document | Purpose |
|---|---|
| [`progress.html`](progress.html) | Stage-by-stage build tracker — open it in a browser |
| [`docs/FRICTION-LOG.md`](docs/FRICTION-LOG.md) | Live friction log (worth up to a 10% judging bonus) |
| [`docs/PRODUCT-FEEDBACK.md`](docs/PRODUCT-FEEDBACK.md) | Required per-SDK product feedback, written as we go |
| [`Assets/hackathon-strategy.html`](Assets/hackathon-strategy.html) | The strategy analysis this project came out of |

## Licence

MIT — see [`LICENSE`](LICENSE).
