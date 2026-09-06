"""Shared test setup.

Loads .env so the opt-in calibration suite can reach Bedrock. Everything else
in the suite runs without credentials and is unaffected.
"""

from recall.config import load_env

load_env()
