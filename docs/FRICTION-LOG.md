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

### The Bedrock console hides the "Model access" page, and account verification is invisible until the first API call
- **Tool / SDK:** Amazon Bedrock console, new AWS account
- **Date:** 2026-09-06
- **Task attempted:** Get a brand-new AWS account to the point of making one Bedrock
  call.
- **Steps taken:** Created the account, enabled MFA, switched to `us-east-1`, went
  looking for the documented **Model access** page in the Bedrock console, then found
  Claude Sonnet 5 through **Model catalog** instead, submitted the Anthropic use-case
  form, created a Bedrock API key, and called `converse()`.
- **Expected:** Either a response, or a clear statement in the console of what was
  still outstanding.
- **Actually happened:** Two separate surprises. First, the widely documented
  standalone "Model access" sidebar entry no longer exists — access is now negotiated
  per model inside the Model catalog. Every guide, including AWS's own, still describes
  the old path, so a newcomer's first act is hunting for a page that is not there.
  Second, and more costly: the call failed with
  `AccessDeniedException: Your account is currently being verified. Verification
  normally takes less than 2 hours.` Nothing anywhere in the console — not the Bedrock
  overview, not the model page, not the account settings — indicated that the account
  was in a pending state. The only way to discover it is to write working code and have
  it rejected.
- **Severity:** major — it is indistinguishable, at the point of failure, from a
  mistake in your own credentials, region, or model id.
- **Workaround:** Wait. The request shape was already correct.
- **Actionable suggestion:** Two things. Surface pending account verification as a
  banner in the console, the way the Anthropic use-case requirement already is — the
  information clearly exists, it is simply not shown where the user is looking. And
  when the old **Model access** page is removed, redirect it rather than deleting it,
  so the years of existing documentation and tutorials still land somewhere useful.

### Claude Sonnet 5 is listed in the model catalogue but cannot be invoked, and the error will not say why
- **Tool / SDK:** Amazon Bedrock, Free plan account
- **Date:** 2026-09-06
- **Task attempted:** Make the first live grading call with
  `us.anthropic.claude-sonnet-5`.
- **Steps taken:** Waited out account verification, then called `converse()`. When it
  failed, called `ListFoundationModels` to see what the account could actually reach,
  then probed five model ids directly.
- **Expected:** Either a response, or an error explaining what to do about it.
- **Actually happened:** `AccessDeniedException: anthropic.claude-sonnet-5 is not
  available for this account. You can explore other available models on Amazon Bedrock.
  For additional access options, contact AWS Sales.` The model is nonetheless returned
  by `ListFoundationModels`, so the catalogue and the runtime disagree. The message
  names no cause and offers no self-service remedy - "contact AWS Sales" is not an
  action a hackathon entrant can take at 11pm. Probing established what the message
  would not: Haiku 4.5 and Sonnet 4.5 both invoke fine on the same account with the
  same key, so it is neither the credentials, nor the region, nor Anthropic access in
  general, nor the use-case form. It is this one model.
- **Severity:** major - three separate hypotheses (bad key, pending use-case form,
  Free plan restriction) all fit the message equally well, and only direct probing
  distinguishes them.
- **Workaround:** Use `us.anthropic.claude-sonnet-4-5-20250929-v1:0`, which works.
- **Actionable suggestion:** Say the reason in the error, and say the remedy. "This
  model requires a Paid account plan" or "requires Marketplace subscription X" turns a
  thirty-minute investigation into a one-click fix. Failing that, exclude models the
  account cannot invoke from `ListFoundationModels`, so the catalogue stops promising
  what the runtime refuses.

### Every Bedrock model exceeds the Alexa+ 500 ms tool budget, including the smallest
- **Tool / SDK:** Amazon Bedrock + Alexa+ MCP Toolkit
- **Date:** 2026-09-06
- **Task attempted:** Measure real round-trip latency against the Alexa+ requirement of
  "less than 500 ms".
- **Steps taken:** Called `converse()` with a sixteen-token cap - about as small as a
  request gets - across four models in `us-east-1`.
- **Expected:** That a small, fast model might fit inside the budget.
- **Actually happened:** Nothing came close. Nova Lite 557 ms, Haiku 4.5 956 ms,
  Sonnet 4.5 1510 ms, and 1771 ms on a repeat call. Amazon's own smallest and cheapest
  model misses Amazon's own latency requirement by 11% on a trivial prompt, before any
  real prompt, retry or cold start.
- **Severity:** major - taken literally, the requirement excludes every model the AWS
  Builder mini challenge exists to encourage.
- **Workaround:** Decision D7 - the tool acknowledges immediately and grades in the
  background, so no single call ever waits on inference.
- **Actionable suggestion:** Either scope the 500 ms budget to the transport
  acknowledgement rather than the whole tool call, or document the async pattern as the
  supported approach for model-backed tools. Right now the two halves of the same
  hackathon point in opposite directions.
