"""
Flask backend for the Debate Partner app.

Session state (conversation history + scorecard) is kept in memory per
session, keyed by a session_id the frontend generates and sends with
every request. This is fine for a demo/student project; a production
version would use a real database or Redis instead of an in-memory dict.
"""

import os
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

from prompts import build_opening_messages, build_rebuttal_messages, build_verdict_messages
from response_parser import parse_debate_response
from scorecard import Scorecard
from groq_client import call_groq

load_dotenv()

app = Flask(__name__)
CORS(app)

MAX_ROUNDS = 6

sessions = {}


@app.route("/api/start", methods=["POST"])
def start_debate():
    data = request.get_json()
    position = data.get("position", "").strip()

    if not position:
        return jsonify({"error": "Position is required"}), 400

    session_id = str(uuid.uuid4())
    messages = build_opening_messages(position)

    try:
        raw_response = call_groq(messages)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    parsed = parse_debate_response(raw_response)
    scorecard = Scorecard()

    if parsed.claim_id:
        scorecard.record_attack(parsed.claim_id, parsed.claim_text)

    history = messages + [{"role": "assistant", "content": raw_response}]

    sessions[session_id] = {
        "history": history,
        "scorecard": scorecard,
        "last_claim": {"claim_id": parsed.claim_id, "claim_text": parsed.claim_text},
        "position": position,
        "round": 1,
    }

    return jsonify({
        "session_id": session_id,
        "rebuttal": parsed.rebuttal_text,
        "claim": {"claim_id": parsed.claim_id, "claim_text": parsed.claim_text},
        "scorecard": scorecard.get_claim_list_for_ui(),
        "round": 1,
        "max_rounds": MAX_ROUNDS,
        "debate_over": False,
    })


@app.route("/api/respond", methods=["POST"])
def respond_to_attack():
    data = request.get_json()
    session_id = data.get("session_id")
    human_response = data.get("response", "").strip()

    if session_id not in sessions:
        return jsonify({"error": "Invalid or expired session_id"}), 400
    if not human_response:
        return jsonify({"error": "Response is required"}), 400

    session = sessions[session_id]
    last_claim = session["last_claim"]

    messages = build_rebuttal_messages(
        session["history"], last_claim["claim_id"], last_claim["claim_text"], human_response
    )

    try:
        raw_response = call_groq(messages)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 500

    parsed = parse_debate_response(raw_response)
    scorecard = session["scorecard"]

    if parsed.previous_claim_status and last_claim["claim_id"]:
        scorecard.record_outcome(last_claim["claim_id"], parsed.previous_claim_status)

    session["round"] += 1
    debate_over = session["round"] > MAX_ROUNDS

    if not debate_over and parsed.claim_id:
        scorecard.record_attack(parsed.claim_id, parsed.claim_text)
        session["last_claim"] = {"claim_id": parsed.claim_id, "claim_text": parsed.claim_text}

    session["history"].append({"role": "user", "content": f'(Human defended claim "{last_claim["claim_id"]}" with): {human_response}'})
    session["history"].append({"role": "assistant", "content": raw_response})

    response_payload = {
        "rebuttal": parsed.rebuttal_text,
        "claim": {"claim_id": parsed.claim_id, "claim_text": parsed.claim_text} if not debate_over else None,
        "scorecard": scorecard.get_claim_list_for_ui(),
        "round": session["round"],
        "max_rounds": MAX_ROUNDS,
        "debate_over": debate_over,
    }

    if debate_over:
        verdict_messages = build_verdict_messages(session["history"], scorecard.get_claim_summary_text())
        try:
            verdict_text = call_groq(verdict_messages, temperature=0.5)
        except RuntimeError as e:
            verdict_text = f"(Could not generate final verdict: {e})"
        response_payload["final_verdict"] = verdict_text
        response_payload["status_counts"] = scorecard.count_by_status()

    return jsonify(response_payload)


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "groq_key_configured": bool(os.environ.get("GROQ_API_KEY"))})


if __name__ == "__main__":
    app.run(debug=True, port=5000)