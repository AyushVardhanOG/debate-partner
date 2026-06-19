"""
Parses an LLM response that contains both natural-language text and a
structured JSON block delimited by ===DEBATE_DATA=== / ===END_DATA===
(see prompts.py for why we do it this way instead of two separate calls).
"""

import json
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedResponse:
    rebuttal_text: str          # the natural-language part, for display
    claim_id: Optional[str]
    claim_text: Optional[str]
    status: Optional[str]                  # "attacking"
    previous_claim_status: Optional[str]   # "defended" / "defeated" / "contested" / None
    raw_response: str           # full original text, kept for debugging


DATA_BLOCK_RE = re.compile(r"===DEBATE_DATA===\s*(\{.*?\})\s*===END_DATA===", re.DOTALL)


def parse_debate_response(raw_text: str) -> ParsedResponse:
    """
    Splits the raw LLM response into the human-readable rebuttal and the
    structured JSON block. If the JSON block is missing or malformed
    (LLMs occasionally don't follow format instructions perfectly), we
    fail gracefully rather than crashing the whole debate.
    """
    match = DATA_BLOCK_RE.search(raw_text)

    if not match:
        return ParsedResponse(
            rebuttal_text=raw_text.strip(),
            claim_id=None,
            claim_text=None,
            status=None,
            previous_claim_status=None,
            raw_response=raw_text,
        )

    rebuttal_text = raw_text[:match.start()].strip()
    json_str = match.group(1)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError:
        return ParsedResponse(
            rebuttal_text=rebuttal_text,
            claim_id=None,
            claim_text=None,
            status=None,
            previous_claim_status=None,
            raw_response=raw_text,
        )

    return ParsedResponse(
        rebuttal_text=rebuttal_text,
        claim_id=data.get("claim_id"),
        claim_text=data.get("claim_text"),
        status=data.get("status"),
        previous_claim_status=data.get("previous_claim_status"),
        raw_response=raw_text,
    )