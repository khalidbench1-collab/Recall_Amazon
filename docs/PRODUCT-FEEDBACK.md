# Product feedback

A **required** submission field. For every tool, API and SDK used: what it was used
for, what worked well, what needs work, how onboarding felt, and whether we would build
with it again. AWS services used must be described here too — that is what qualifies
the AWS Builder mini challenge.

Written incrementally as each dependency is adopted, for the same reason as the
friction log: fresh impressions are specific, remembered ones are generic.

## Template

```
## <tool / SDK / service>
- **Used for:** 
- **Onboarding:** 
- **Worked well:** 
- **Needs work:** 
- **Would build with it again:** yes | with reservations | no — because…
```

---

## Model Context Protocol (spec 2025-11-25, Streamable HTTP)
- **Used for:** The entire public surface. Recall is an MCP server, not an app with an
  MCP adapter bolted on; Alexa+ is one client among several.
- **Onboarding:** Fast. A hello-world server and a real client handshake took under an
  hour, and `initialize` negotiated `2025-11-25` without any version pinning on our
  side.
- **Worked well:** Client-agnosticism is the feature. It is why this project needed no
  Alexa hardware to build: MCP Inspector, Claude Code, a Python client and a browser
  harness all exercise the same code path a device would.
- **Needs work:** The 500 ms expectation downstream sits awkwardly with a protocol that
  has progress notifications for exactly this reason; guidance on slow tools would help.
- **Would build with it again:** Yes.

## FastMCP
- **Used for:** Serving the four tools over Streamable HTTP.
- **Onboarding:** A working server in about six lines.
- **Worked well:** Decorator-based tool registration, and type hints becoming the tool
  schema with no duplication.
- **Needs work:** It serves `/mcp` and 307-redirects `/mcp/`, so a trailing slash
  silently costs a round trip per call — not free when something upstream is enforcing
  500 ms. The startup banner does not make the canonical path obvious.
- **Would build with it again:** Yes.

## Amazon Bedrock
- **Used for:** The semantic grader — the component the whole project rests on.
  `src/recall/grader.py` calls the **Converse API** on `bedrock-runtime` with a system
  prompt that scores a transcribed spoken answer against the expected one and returns
  a 0–5 quality plus one short sentence to be read aloud. That number is fed straight
  into SM-2, an algorithm that has required a 0–5 self-assessment since 1987 and never
  had an honest way to obtain one. Model: `us.anthropic.claude-sonnet-4-6`, US geo
  inference profile, `us-east-1`, `temperature=0`, 200-token cap. Credentials are a
  **Bedrock API key** (`AWS_BEARER_TOKEN_BEDROCK`) rather than IAM access keys.
  Calibration evidence is in `docs/CALIBRATION.md` and reproducible with
  `RECALL_CALIBRATION=1 pytest tests/test_calibration.py`.
- **Onboarding:** Rough, and every rough edge is in the friction log with a suggested
  fix. A new account is silently unverified for up to two hours and the only way to
  discover that is a rejected API call. The standalone **Model access** console page
  that every tutorial references no longer exists. Claude Sonnet 5 is returned by
  `ListFoundationModels` but refuses to invoke on a Free plan account, with an error
  that names no cause and offers no self-service remedy. Working out that the problem
  was one specific model — not the key, the region, the use-case form, or Anthropic
  access in general — took a five-model probe that the error message should have made
  unnecessary.
- **Worked well:** The Converse API is genuinely good. One call shape across providers
  meant swapping Sonnet 5 → Sonnet 4.5 → Sonnet 4.6 was a one-line environment change
  with no code edit, which is exactly what you want when availability is uncertain.
  `temperature=0` plus a JSON-only instruction gave stable, well-formed output: the
  calibration suite passed 11 of 11 bands on its **first** live run, including the case
  that matters most — an answer whose key word was mangled by transcription
  (*"leemah"*) still scored 5, because the model graded meaning rather than characters.
  Bedrock API keys are a real improvement over minting IAM users for a prototype.
- **Needs work:** Two things, both about honesty of information. Availability is
  advertised in one place and enforced in another, so the catalogue promises models the
  runtime refuses. And latency: on a sixteen-token prompt we measured Nova Lite at
  557 ms, Haiku 4.5 at 956 ms, Sonnet 4.6 at 1054 ms and Sonnet 4.5 at 1510 ms — every
  one of them over the **500 ms round-trip budget the Alexa+ MCP Toolkit requires**.
  Two parts of the same hackathon currently point in opposite directions, and the
  resolution had to be architectural (see D7).
- **Would build with it again:** Yes. The onboarding cost us an afternoon; the API
  itself cost us nothing and the grading quality is the reason the project works.

## Alexa+ developer tooling (MCP Toolkit documentation)
- **Used for:** Establishing what a self-hosted MCP server must satisfy to connect to
  Alexa+, and deciding the architecture from that.
- **Onboarding:** The quickstart is clear about mechanics - `alexa-ai configure`,
  `alexa-ai deploy`, an add-on manifest - but never states whether Preview enrolment is
  a precondition, which is the single question a new entrant arrives with. Preview-gated
  products should state their gate before their prerequisites, because it is the only
  prerequisite a reader cannot fix by reading further.
- **Worked well:** The requirements are specific and testable rather than vague, which
  is rarer than it should be: a named spec version (2025-11-25), a named transport
  (Streamable HTTP), a named auth flow (OAuth 2.1 authorization code with PKCE S256),
  and an explicit list of what is *not* supported (DCR, OIDC, CIMD). That list saved
  real time - knowing what is unsupported is worth more than knowing what is.
- **Needs work:** The **500 ms round-trip budget** is the significant one, and it is
  stated as a flat number with no guidance for tools whose work is genuinely slower. We
  measured every plausible Bedrock model on a sixteen-token prompt and all of them miss
  it, Amazon's own Nova Lite included at 557 ms. Taken literally the requirement
  excludes every AI-backed add-on, which is the category the toolkit exists to enable
  and the AWS Builder mini challenge exists to encourage. The MCP spec has progress
  notifications for exactly this situation and the docs do not mention them. We resolved
  it architecturally - acknowledge in 18 ms, grade in the background - but that was our
  inference, not documented guidance, and every entrant will have to rediscover it.
- **Would build with it again:** Yes. The protocol choice is right, and being
  client-agnostic meant no hardware was ever needed. The latency budget needs either
  scoping to the transport acknowledgement or a documented pattern for slow tools.
