"""Semantic grading of a spoken answer, via Amazon Bedrock.

Runs server-side by design (decision D3): keeping the scoring prompt and its
calibration inside this repo is what makes the grading ours rather than the
calling platform's, and is what qualifies the AWS Builder mini challenge.
"""

raise_on_import = None  # placeholder module; implemented in stage 4
