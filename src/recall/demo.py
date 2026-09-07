"""A fixed deck for demos and for the submission video.

Grading is non-deterministic, so the deck must not be. Every card here is
chosen so that a *partially* correct spoken answer is natural and obvious - the
demo has ninety seconds to show that the grader scores meaning rather than
wording, and it cannot do that with cards whose answers are single words.
"""

from __future__ import annotations

from datetime import datetime

from recall.store import Store

DEMO_DECK: list[tuple[str, str]] = [
    (
        "What does the ease factor in SM-2 control?",
        (
            "How fast a card's interval grows. Each successful review "
            "multiplies the interval by the ease factor."
        ),
    ),
    (
        "Why does spaced repetition work better than re-reading?",
        (
            "Retrieval strengthens memory more than recognition does. "
            "Struggling to recall something is what consolidates it."
        ),
    ),
    (
        "What is the difference between mitosis and meiosis?",
        (
            "Mitosis produces two identical diploid cells for growth and "
            "repair. Meiosis produces four genetically distinct haploid gametes."
        ),
    ),
    (
        "What did the Treaty of Westphalia establish?",
        (
            "The principle of state sovereignty - that states have exclusive "
            "authority within their own borders and do not interfere in each "
            "other's internal affairs."
        ),
    ),
    (
        "In Spanish, when do you use ser rather than estar?",
        (
            "Ser is for permanent or defining qualities like identity and "
            "origin. Estar is for temporary states, locations and conditions."
        ),
    ),
    (
        "What problem does the Model Context Protocol solve?",
        (
            "It gives assistants one standard way to discover and call external "
            "tools, so an integration written once works across any client that "
            "speaks the protocol."
        ),
    ),
    (
        "Why is the speed of light the same for all observers?",
        (
            "Because it follows from Maxwell's equations, which contain no "
            "reference frame. Special relativity takes that as a postulate and "
            "lets time and space adjust instead."
        ),
    ),
    (
        "What is an append-only log, and why use one?",
        (
            "A store where records are only ever added, never edited or "
            "deleted. It preserves history, so past state can be reconstructed "
            "and audited."
        ),
    ),
]


def seed(store: Store, *, now: datetime) -> int:
    """Load the demo deck, skipping cards that are already there.

    Idempotent on purpose. A demo gets re-recorded, and the second take should
    not face twice the review pile of the first.
    """
    existing = store.list_prompts()
    added = 0
    for prompt, answer in DEMO_DECK:
        if prompt in existing:
            continue
        store.add_card(prompt, answer, created_at=now)
        added += 1
    return added
