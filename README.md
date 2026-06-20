# Debate Partner

An AI that argues *against* you — not with you. State a position, and a formal debate opponent attacks your weakest claim, evaluates how well you defend it, and tracks the outcome of every point across a live scoreboard. Ends with a final verdict on whether your position held up under pressure.

## Why this exists

Most AI chat tools are agreeable by default. This one is built specifically to find holes in your thinking — useful for debate prep, pressure-testing a pitch or argument, or sharpening reasoning before a real conversation where someone else will push back for real.

## What makes it different from a regular chatbot

- **Surgical attacks** — the AI attacks exactly one claim per turn, not your whole argument at once, the way a real debate opponent would.
- **Persistent scoreboard** — every claim is tracked across the whole debate: defended, defeated, or contested. The AI adapts its strategy as the debate progresses.
- **Structured + natural output in one model call** — each response carries both a human-readable rebuttal and machine-readable state, kept in a single call to stay free to run.
- **Final verdict** — after 6 rounds, a formal summary of which points held up and which collapsed.

## Tech stack

Python, Flask, JavaScript, Groq API (Llama 3.3 70B)

## Project structure

backend/    — Flask API, prompt engineering, scoring logic

frontend/   — single-file UI (debate transcript + live scoreboard)

## Try it

[Live demo link here once deployed]