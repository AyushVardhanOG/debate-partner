"""
Tracks the state of every claim across a debate session.

This is what gives the tool "memory" — without this, each AI response
would be evaluated in isolation, with no way to build a final scorecard
of which points held up and which collapsed.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Claim:
    claim_id: str
    claim_text: str
    status: str  # "attacking" (currently being attacked) / "defended" / "defeated" / "contested"
    rounds_attacked: int = 1


class Scorecard:
    def __init__(self):
        self.claims: Dict[str, Claim] = {}
        self.round_number: int = 0

    def record_attack(self, claim_id: str, claim_text: str):
        """Called when the AI attacks a claim (new or returning to an old one)."""
        self.round_number += 1
        if claim_id in self.claims:
            self.claims[claim_id].status = "attacking"
            self.claims[claim_id].rounds_attacked += 1
        else:
            self.claims[claim_id] = Claim(claim_id=claim_id, claim_text=claim_text, status="attacking")

    def record_outcome(self, claim_id: str, outcome_status: str):
        """
        Called with the PREVIOUS claim's outcome, reported by the AI on
        the NEXT turn (since the AI evaluates the human's response to
        the previous attack before issuing the new one).
        """
        if claim_id and claim_id in self.claims and outcome_status:
            self.claims[claim_id].status = outcome_status

    def get_claim_summary_text(self) -> str:
        """Plain-text summary for feeding into the final verdict prompt."""
        if not self.claims:
            return "No claims were tracked during this debate."

        lines = []
        for claim in self.claims.values():
            lines.append(f"- [{claim.status.upper()}] {claim.claim_text} (attacked {claim.rounds_attacked} time(s))")
        return "\n".join(lines)

    def get_claim_list_for_ui(self) -> List[dict]:
        """JSON-serializable list for sending to the frontend."""
        return [
            {
                "claim_id": c.claim_id,
                "claim_text": c.claim_text,
                "status": c.status,
                "rounds_attacked": c.rounds_attacked,
            }
            for c in self.claims.values()
        ]

    def count_by_status(self) -> dict:
        counts = {"defended": 0, "defeated": 0, "contested": 0, "attacking": 0}
        for claim in self.claims.values():
            if claim.status in counts:
                counts[claim.status] += 1
        return counts