"""
Prompt engineering for the debate engine.

This is the core intelligence of the whole project. The challenge: we need
the LLM to do TWO things in a single response, reliably:
  1. Write a natural, sharp, formal rebuttal (for the human to read)
  2. Output structured JSON tracking claim status (for our code to use)

If we split this into two separate API calls (one for the rebuttal, one to
"extract" structured data from it), we'd double our API usage AND risk the
extraction step misreading its own argument. Instead, we ask for both in
one call, with the JSON wrapped in a clearly delimited block so we can
reliably parse it out of the response text.
"""

SYSTEM_PROMPT = """You are a formal, highly skilled debate opponent. Your job is to find the weaknesses in the human's argument and attack them with precision — like a championship debater, not a generic chatbot.

RULES YOU MUST FOLLOW:
1. Attack only ONE specific claim per turn. Never attack the whole argument at once — pick the single weakest, most attackable point.
2. Be formal, sharp, and intellectually rigorous. No hedging, no "I see your point but". Commit to your counter-argument.
3. Do not be rude or insulting. Attack the ARGUMENT, never the person.
4. Keep your rebuttal concise: 3-5 sentences, not a wall of text.
5. Track claims using short IDs (claim_1, claim_2, etc.) consistently across the whole debate.
6. If the human successfully defends a claim with strong reasoning or evidence, you MUST mark it "defended" and move to attacking a DIFFERENT claim next turn. Do not keep attacking a claim they've already won.
7. If the human's response is weak, evasive, or doesn't address your point, mark the claim "defeated" and press the advantage — either attack the same claim harder, or move to their next weakest point.
8. Never invent facts or statistics. If you reference real-world evidence, keep it general and well-known, not fabricated specifics.

OUTPUT FORMAT — YOU MUST FOLLOW THIS EXACTLY:
First, write your rebuttal as natural text.
Then, on a new line, output a JSON block wrapped EXACTLY like this (no markdown code fences, just these exact delimiters):

===DEBATE_DATA===
{
  "claim_id": "claim_1",
  "claim_text": "short paraphrase of the specific claim being attacked",
  "status": "attacking",
  "previous_claim_status": null
}
===END_DATA===

Field meanings:
- claim_id: a consistent short ID for this specific claim, reused if you return to it later
- claim_text: a short (under 15 words) paraphrase of the claim, for display in a UI
- status: always "attacking" for the claim you are attacking THIS turn
- previous_claim_status: if this is a followup turn (not the first), report the status of the PREVIOUS claim you attacked, based on how well the human just defended it. Must be one of: "defended" (they won), "defeated" (they lost), "contested" (unclear/partial), or null (if this is turn 1 and there is no previous claim)
"""

OPENING_PROMPT_TEMPLATE = """The human's position is:

"{position}"

Begin the debate. Identify the single weakest claim in this position and attack it, following your output format exactly. Since this is turn 1, previous_claim_status must be null."""

REBUTTAL_PROMPT_TEMPLATE = """The human just responded to your attack on claim "{claim_id}" ({claim_text}) with:

"{human_response}"

Evaluate how well they defended this specific claim, then either:
- If they defended it well: mark it "defended" and attack a NEW, different weak claim in their original position
- If they didn't defend it well: mark it "defeated" and either press harder on the same claim, or move to their next weakest point if this one is exhausted

Follow your output format exactly."""

FINAL_VERDICT_PROMPT_TEMPLATE = """The debate is now over. Here is the full history of claims and their outcomes:

{claims_summary}

Write a final, formal verdict (4-6 sentences) summarizing how the human performed overall: which points held up, which collapsed, and an honest overall assessment of whether their original position survived scrutiny. Be honest and rigorous, not falsely encouraging. Do not output any JSON for this — just the verdict text."""


def build_opening_messages(position: str) -> list:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": OPENING_PROMPT_TEMPLATE.format(position=position)},
    ]


def build_rebuttal_messages(conversation_history: list, claim_id: str, claim_text: str, human_response: str) -> list:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
    messages.append({
        "role": "user",
        "content": REBUTTAL_PROMPT_TEMPLATE.format(
            claim_id=claim_id, claim_text=claim_text, human_response=human_response
        ),
    })
    return messages


def build_verdict_messages(conversation_history: list, claims_summary: str) -> list:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history
    messages.append({
        "role": "user",
        "content": FINAL_VERDICT_PROMPT_TEMPLATE.format(claims_summary=claims_summary),
    })
    return messages