"""The demo deck has to be reproducible: the video depends on it."""

from datetime import UTC, datetime

import pytest

from recall.demo import DEMO_DECK, seed
from recall.store import Store

NOW = datetime(2026, 9, 6, 9, 0, tzinfo=UTC)


@pytest.fixture
def store(tmp_path):
    with Store.open(tmp_path / "demo.db") as s:
        yield s


def test_seeding_creates_every_card_in_the_deck(store: Store) -> None:
    seed(store, now=NOW)
    assert len(store.list_due_cards(now=NOW)) == len(DEMO_DECK)


def test_every_seeded_card_is_due_immediately(store: Store) -> None:
    seed(store, now=NOW)
    assert all(card.due_at == NOW for card in store.list_due_cards(now=NOW))


def test_seeding_twice_does_not_duplicate_the_deck(store: Store) -> None:
    """A second take of the demo must not double the review pile."""
    seed(store, now=NOW)
    seed(store, now=NOW)
    assert len(store.list_due_cards(now=NOW)) == len(DEMO_DECK)


def test_the_deck_has_no_duplicate_prompts() -> None:
    prompts = [prompt for prompt, _ in DEMO_DECK]
    assert len(set(prompts)) == len(prompts)
