"""Stage 1 spike: one live Bedrock call, nothing more.

Uses the Converse API against the US geo inference profile. Note the profile
prefix is not optional for Sonnet 5: the model card marks In-Region as
unsupported in every US region, so `anthropic.claude-sonnet-5` on its own will
fail. `us.` (or `global.`) is required.
"""

import os
from pathlib import Path

import boto3


def load_env(path: Path = Path(".env")) -> None:
    """Read KEY=VALUE lines from .env into the environment.

    Hand-rolled rather than pulling in python-dotenv: six lines is cheaper than
    a dependency for a spike, and it keeps the secret in a gitignored file
    instead of a shell command that would land in shell history.
    """
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


load_env()

MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-sonnet-5")
REGION = os.environ.get("AWS_REGION", "us-east-1")

client = boto3.client("bedrock-runtime", region_name=REGION)
response = client.converse(
    modelId=MODEL_ID,
    messages=[{"role": "user", "content": [{"text": "Reply with the single word: ready"}]}],
    inferenceConfig={"maxTokens": 16},
)
print(response["output"]["message"]["content"][0]["text"])
print("latency_ms:", response["metrics"]["latencyMs"])
