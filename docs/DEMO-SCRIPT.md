# Demo video script

**Limit: 3 minutes. Target: 2:10.** Judges are not required to watch past three
minutes, so nothing important may appear after 1:30.

**The one thing this video must prove:** that Recall grades what you *meant*. Everything
else — architecture, MCP, Bedrock — is support. If a judge watches only the first
twenty seconds, they should already have seen a wrong-ish spoken answer scored fairly.

---

## Before recording

- [ ] `python scripts/seed_demo.py` on a **fresh** database, so the deck is the known one
- [ ] Run one full review privately first — grading is non-deterministic, and you want
      to know roughly what it says before the take
- [ ] Browser at 125% zoom; the harness is dark-themed and reads well on video
- [ ] Close notifications, other tabs, and anything with a name in it
- [ ] Headphones **off** so the mic does not pick up the synthesised voice
- [ ] Record at 1080p. No music — the rules forbid unlicensed audio, and there is
      nothing to gain from it

---

## The script

### 0:00–0:08 — Cold open, no preamble

> *(screen: the harness, already running. Click Start review.)*

**Recall speaks:** "You're on a 1 day streak, and 8 cards due."
**Recall speaks:** "What does the ease factor in SM-2 control?"

**You say, to camera or over the top:**
> "This is a flashcard app you answer out loud. Watch what happens when I get it
> *almost* right."

Say nothing else yet. The next fifteen seconds are the entire pitch.

### 0:08–0:35 — The payoff

> *(click Hold to answer, then speak — deliberately imprecise, with filler)*

**You say aloud:**
> "um it decides how much bigger the gap gets each time you get it right"

**On screen:** `acknowledged in 18 ms — grading continues in the background`

**Recall speaks:** *(roughly)* "Good, but you missed that the ease factor multiplies
the interval each successful review. I'll ask you again tomorrow."

**You say:**
> "That answer had none of the same words as the card. It wasn't marked wrong, and it
> wasn't marked right — it got a four out of five, and the card comes back tomorrow
> instead of in three months."

### 0:35–1:05 — Why that number is the whole point

> *(screen: `docs/CALIBRATION.md`, scroll slowly)*

**You say:**
> "SM-2, the spaced repetition algorithm, has needed a zero-to-five quality score since
> 1987. Every flashcard app collects it by asking you to rate yourself — *after* it has
> shown you the answer, which is exactly when nobody can judge themselves honestly.
>
> Recall fills that slot from outside. You answer before you see anything, and a model
> on Bedrock scores it. Here are eleven calibration cases with the bands a fair teacher
> would accept. Eleven out of eleven landed inside, first run."

> *(stop scrolling on the "leemah" row)*

> "This one is my favourite. The speech recogniser heard 'leemah' instead of 'Lima'. A
> string comparison marks that wrong. It scored five, because it graded the meaning."

### 1:05–1:35 — How it is built

> *(screen: the architecture diagram in README, then the terminal showing the server)*

**You say:**
> "It's a self-hosted MCP server over Streamable HTTP — spec 2025-11-25 — so Alexa+ can
> drive it, and so can anything else. What you just saw was a browser harness speaking
> the same protocol to the same endpoint.
>
> One constraint shaped the design. Alexa+ gives a tool call about 500 milliseconds. The
> fastest model on Bedrock took 557 on a sixteen-token prompt — everything is over
> budget. So answering and grading are two separate tools. The answer is acknowledged in
> eighteen milliseconds and graded behind it. That's the number you saw on screen."

### 1:35–2:00 — The part that is easy to get wrong

**You say:**
> "One design rule I want to point at. If the speech recogniser fails, or Bedrock is
> down, the card's schedule is left completely untouched. A recognition failure is not a
> memory failure, and a silently mis-scheduled card is worse than a skipped review.
> There's a test asserting the card is byte-identical afterwards."

### 2:00–2:10 — Close

**You say:**
> "Recall. Voice-native spaced repetition, MIT licensed, and the friction log from
> building it is in the repo."

---

## Discipline

- [ ] The harness is **visibly labelled SIMULATED** — do not crop that banner out. The
      rules permit a simulated experience; implying real device footage is a
      disqualification risk.
- [ ] No Alexa device imagery, no Amazon logos, no third-party trademarks
- [ ] No music, licensed or otherwise
- [ ] English throughout
- [ ] Upload public on YouTube, and **watch it once logged out** to confirm it plays

## If a take goes wrong

Grading is non-deterministic; a score may land one band off. That is not a failed take
— it is the honest behaviour of the system, and a slightly different explanation is
fine. Re-record only if the score is *unfair*, and if that happens, keep the footage:
an honest note about a miscalibrated case is better material for the write-up than
pretending it never occurred.
