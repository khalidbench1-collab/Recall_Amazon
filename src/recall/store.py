"""SQLite persistence for cards and the append-only review log.

The review log is kept separate from card state deliberately: it is what makes
streak and retention reporting possible, and what lets grader calibration be
evaluated retrospectively against real attempts.
"""

raise_on_import = None  # placeholder module; implemented in stage 3
