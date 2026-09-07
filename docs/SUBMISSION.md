# Devpost submission — draft text

Paste-ready answers for each required field. Review before submitting; the numbers are
current as of 7 September 2026 and should be re-checked at submission time.

---

## Project name

**Recall**

## Tagline

Voice-native spaced repetition. Answer out loud; graded on meaning, not wording.

---

## What it does (text description)

Recall is a self-hosted **MCP server** that turns spaced repetition into something you
do out loud — while cooking, driving, or walking — and grades what you actually said for
*meaning* rather than exact wording.

**The idea underneath it.** SM-2, the spaced repetition algorithm, has required a 0–5
quality score for every review since 1987. Every flashcard app in existence collects
that score by making you tap *Again / Hard / Good / Easy* — a self-assessment made
*after* you have already seen the correct answer, which is precisely the moment people
are worst at judging themselves. The algorithm has had a slot for an honest signal for
thirty years, and no interface could fill it.

Recall fills it. You answer aloud before seeing anything, and a semantic grader on
Amazon Bedrock scores the answer from outside, returning a 0–5 quality and one short
sentence to be read back. That number goes straight into the scheduler.

**What that buys you, concretely.** In the calibration suite, a learner whose answer was
transcribed as *"the capital of peru is leemah"* scored **5** — a string comparison marks
that wrong; the grader read the meaning. An answer that was confidently wrong scored 0,
while "honestly I have no idea" also scored 0 but for a different reason the explanation
names. Eleven of eleven calibration cases landed inside their expected bands on the
first live run; the evidence is generated into `docs/CALIBRATION.md` so a reader can
judge the fairness rather than take our word for it.

**How it works.** Five MCP tools over Streamable HTTP (spec 2025-11-25): `add_card`,
`next_due_card`, `submit_answer`, `get_grade`, `get_streak_summary`. A SQLite store
holds card state plus an append-only review log; the SM-2 scheduler is pure functions
with an injected clock; the grader calls Amazon Bedrock.

**One constraint shaped the architecture.** The Alexa+ MCP Toolkit requires a round-trip
tool latency of **under 500 ms**. We measured every candidate model on a sixteen-token
prompt: Amazon Nova Lite 557 ms, Claude Haiku 4.5 956 ms, Claude Sonnet 4.6 1054 ms,
Claude Sonnet 4.5 1510 ms. Every model is over budget before the prompt is even real. So
grading is split in two: `submit_answer` records the answer and returns in **18 ms**,
and `get_grade` collects the verdict once it exists. It also turns out to be better
conversation than blocking would have been — "let me think", then an answer, is how
people talk; four seconds of silence is a fault.

**A design rule worth stating.** If speech recognition fails, or Bedrock is unavailable,
or the model returns something unparseable, the card's schedule is left **completely
untouched**. A recognition failure is not a memory failure, and a silently mis-scheduled
card is worse than a skipped review. There is a test asserting the card is byte-identical
after an ungraded answer.

**Running it.** `git clone`, `pip install -e ".[dev]"`, `pytest`, `python -m
recall.server`. Verified by cloning the published repo into an empty directory and
following the README literally. It runs **without an AWS account** — everything except
grading works, and the server says so at startup.

---

## Track

**Alexa+** — a self-hosted MCP server implementing spec 2025-11-25 over Streamable HTTP.
A browser harness at `sim/index.html`, served from the MCP server's own origin, drives
the identical endpoint by voice using the Web Speech API and is clearly labelled as a
simulated experience.

## Mini challenges

**AWS Builder** and **Open Source**.

---

## AWS Builder — which AWS services, and how

**Amazon Bedrock**, via the **Converse API** on the `bedrock-runtime` endpoint, called
from `src/recall/grader.py`.

- **Model:** `us.anthropic.claude-sonnet-4-6` (US geo inference profile), `us-east-1`,
  `temperature=0`, 200-token cap.
- **What it does:** scores a transcribed spoken answer against the expected answer,
  returning `{"quality": 0-5, "explanation": "..."}`. The quality feeds SM-2 directly;
  the explanation is length-capped and read aloud.
- **Why server-side:** letting the calling assistant grade would have been less code,
  but it would reduce this project to a card database, put the interesting behaviour
  outside the repository where it cannot be assessed, and leave nothing of ours to
  calibrate. The scoring prompt and its calibration are the artefact.
- **Credentials:** a Bedrock API key (`AWS_BEARER_TOKEN_BEDROCK`), scoped to Bedrock by
  construction rather than a broadly-permissioned IAM user.
- **Reproduce the evidence:** `RECALL_CALIBRATION=1 pytest tests/test_calibration.py`.

Full write-up, including what worked and what did not, in `docs/PRODUCT-FEEDBACK.md`.

---

## Open Source — contribution

- **Project repository:** https://github.com/khalidbench1-collab/Recall_Amazon (MIT)
- **Contribution URL:** https://github.com/khalidbench1-collab/fastmcp/tree/banner-server-url
- **GitHub username:** khalidbench1-collab

**What it does.** FastMCP's startup banner prints the server name and a deploy link, but
not the URL the server is actually listening on. With HTTP transport that address is
already resolved a few lines above the banner call — the one thing a client needs is
known and not shown.

**Why it matters.** The canonical endpoint is `/mcp`, and `/mcp/` is served by a 307
redirect. A client configured from a guess therefore spends an extra round trip on every
call, or fails outright if it does not follow redirects on POST. We hit this while
building Recall, and it is not free: the Alexa+ latency budget upstream is 500 ms.

**How it works.** `log_server_banner` takes an optional `url`; `run_http_async` resolves
the path exactly as `http_app` does, including the `sse_path` / `streamable_http_path`
defaults. stdio passes nothing and the row is omitted, since stdio has no address. Three
tests cover the URL being shown, the row being omitted without one, and the existing
server-name row still rendering.

---

## Friction log

`docs/FRICTION-LOG.md` — captured live from day one, not reconstructed. Seven entries,
three rated major, each with severity, workaround and an actionable suggestion.

Headlines:

1. **Every Bedrock model exceeds the Alexa+ 500 ms tool budget**, including Amazon's own
   smallest. Two halves of the same hackathon currently point in opposite directions.
2. **Claude Sonnet 5 is returned by `ListFoundationModels` but refuses to invoke**, with
   an error naming no cause and no self-service remedy. Establishing that the problem was
   one specific model — not the key, region, use-case form, or Anthropic access in
   general — took a five-model probe the message should have made unnecessary.
3. **A new AWS account is silently unverified for up to two hours**, and nothing in the
   console says so. The only way to find out is to write correct code and have it
   rejected.
4. The Bedrock model card's own **sample code contradicts its availability table** two
   sections above it.
5. The **Model access console page** every tutorial references no longer exists.

---

## Feature requests (optional field)

1. **Scope or waive the 500 ms Alexa+ budget for model-backed tools** — *critical.* As
   written it excludes the category of add-on the AWS Builder challenge encourages.
   Either scope it to the transport acknowledgement, or document the async pattern as
   supported.
2. **Say why a Bedrock model is unavailable, and how to fix it** — *important.* "Requires
   a Paid account plan" turns a thirty-minute investigation into one click.
3. **Surface pending account verification in the console** — *important.* The information
   exists; it is simply not shown where a new user is looking.
4. **State Alexa+ Preview eligibility at the top of the MCP Toolkit quickstart** —
   *nice-to-have.* It is the one prerequisite a reader cannot fix by reading further.

---

## Pre-submission checks

- [ ] Repo public, MIT licence visible in the **About** panel
- [ ] Demo video public on YouTube, under 3 minutes, English, no licensed music
- [ ] Video shows the harness with its **SIMULATED** label intact
- [ ] Contribution URL, repo URL and GitHub username entered in the Open Source fields
- [ ] AWS services described in the product feedback answer
- [ ] Both mini challenges declared alongside the Alexa+ track
- [ ] Submitted with days to spare — the form has more fields than anyone expects
