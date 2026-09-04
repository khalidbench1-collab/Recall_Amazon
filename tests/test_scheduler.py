"""SM-2 scheduling tests.

Written first, in stage 2. The scheduler is the component where correctness
matters most and is cheapest to verify, which is why it leads the build.
"""

import pytest

from recall.scheduler import CardState, review


@pytest.mark.skip(reason="stage 2 - scaffolding only")
def test_placeholder() -> None:
    assert review(CardState(0, 0, 2.5), 5)
