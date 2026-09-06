# Friction log

Captured live while building. Reconstructing this at the end produces something
obviously thin; the hackathon awards up to a **10% judging bonus** for it, and most
entrants will skip it because it is optional.

**Log an entry the moment something surprises you.** Bad error message, missing doc,
confusing auth flow, a default that did the wrong thing. Do not wait.

## Entry template

Copy this block for each entry.

```
### <short title>
- **Tool / SDK:** 
- **Date:** 
- **Task attempted:** 
- **Steps taken:** 
- **Expected:** 
- **Actually happened:** 
- **Severity:** blocker | major | minor | cosmetic
- **Workaround:** 
- **Actionable suggestion:** 
```

---

## Entries

### Establishing whether an Alexa+ MCP server can be tested without a device
- **Tool / SDK:** Alexa+ developer documentation
- **Date:** 2026-09-04
- **Task attempted:** Determine, before committing to the track, whether a self-hosted
  MCP server can be exercised against a real Alexa+ account during Preview.
- **Steps taken:** Read the hackathon track requirements and resources listing.
- **Expected:** A clear statement of what Preview access a hackathon entrant gets.
- **Actually happened:** Resolved on 2026-09-06. There is a documented path — the
  **Alexa+ MCP Toolkit** — which connects a self-hosted MCP server to Alexa+ via an
  add-on, using the `alexa-ai` CLI (`configure`, `deploy`) and an existing Alexa
  developer account. The quickstart never states whether Preview enrolment is a
  precondition, which is the friction: the one question a new entrant arrives with is
  the one the page does not answer. It also requires a **publicly reachable URL**, so
  local development needs a tunnel (the docs suggest `cloudflared`).
- **Severity:** minor — slows the decision, does not block it.
- **Workaround:** The rules sanction a simulated web-app experience, so the browser
  harness covers this either way.
- **Actionable suggestion:** Put an explicit "who can use this today" box at the top of
  the MCP Toolkit quickstart. Preview-gated products should state their gate first,
  before the prerequisites, because that is the only prerequisite a reader cannot fix.

### The Alexa+ 500 ms latency budget is incompatible with a model call inside a tool
- **Tool / SDK:** Alexa+ MCP Toolkit
- **Date:** 2026-09-06
- **Task attempted:** Confirm the requirements a Recall tool call must satisfy.
- **Steps taken:** Read the MCP Toolkit quickstart prerequisites.
- **Expected:** Transport and auth requirements.
- **Actually happened:** Found an additional hard requirement: "round-trip query
  response latency of less than 500 ms". Any MCP tool that calls a language model
  server-side will exceed this — a Bedrock Converse call to Sonnet 5 is seconds, not
  milliseconds. The requirement is stated as a flat number with no guidance on what a
  server should do when its work is genuinely slower, and no mention of progress
  notifications, which the MCP spec provides precisely for this case.
- **Severity:** major — it constrains the architecture of any AI-backed add-on, which
  is most of them.
- **Workaround:** Under evaluation. See decision D7 in the design spec.
- **Actionable suggestion:** State whether the budget covers the whole tool call or
  only the transport acknowledgement, and if the former, document the sanctioned
  pattern for slow tools. As written, the number rules out the category of add-on the
  toolkit exists to enable.

### FastMCP serves Streamable HTTP at `/mcp`, and redirects `/mcp/` with a 307
- **Tool / SDK:** FastMCP 4.0.3
- **Date:** 2026-09-06
- **Task attempted:** Connect a client to the spike server.
- **Steps taken:** Started `spike/hello_mcp.py`, connected with `fastmcp.Client` at
  `http://127.0.0.1:8765/mcp/`.
- **Expected:** A direct POST to the endpoint.
- **Actually happened:** Every request cost two round trips — a 307 from `/mcp/` to
  `/mcp`, then the real POST. It works, because the client follows redirects on POST,
  but a stricter client would drop the body and fail with something unhelpful. The
  server's own startup banner does not make the canonical path obvious.
- **Severity:** minor — silent cost, not a failure.
- **Workaround:** Use `/mcp` with no trailing slash everywhere, including `.mcp.json`.
- **Actionable suggestion:** Either serve both paths directly or log the canonical URL
  once at startup. Given a 500 ms latency budget upstream, a free extra round trip per
  call is not a cosmetic detail.

### Claude Sonnet 5 on Bedrock cannot be called by its bare model id in any US region
- **Tool / SDK:** Amazon Bedrock
- **Date:** 2026-09-06
- **Task attempted:** Confirm the model id and region before writing `grader.py`.
- **Steps taken:** Read the Claude Sonnet 5 model card.
- **Expected:** `anthropic.claude-sonnet-5` usable in `us-east-1`.
- **Actually happened:** The regional availability table marks **In-Region as
  unsupported in every US region**; only Geo (`us.`) and Global (`global.`) work. Yet
  the Sample Code section on the same page passes the bare `anthropic.claude-sonnet-5`
  to `converse()` with `region_name='us-east-1'` — a combination the table two
  sections above says is unavailable. Copying the sample verbatim is the first thing a
  reader does.
- **Severity:** major — the documented sample contradicts the documented support
  matrix.
- **Workaround:** Always use the `us.` geo profile. `.env.example` already does.
- **Actionable suggestion:** Generate the sample code from the availability table
  rather than from a template, so the two cannot drift apart.
