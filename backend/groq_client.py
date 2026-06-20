"""
Thin wrapper around the Groq API. Groq's API is OpenAI-compatible, so we
use simple HTTP requests rather than pulling in a heavy SDK.
"""

import os
import requests

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"  # strong enough for real argumentation


def call_groq(messages: list, temperature: float = 0.7) -> str:
    """
    Sends a chat completion request to Groq. Returns the raw text response.
    Raises a clear exception if the API key is missing or the request fails,
    rather than failing silently.
    """
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY environment variable is not set. "
            "Create a .env file with GROQ_API_KEY=your_key_here, or set it in your shell."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 600,
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload, timeout=30)

    if response.status_code != 200:
        raise RuntimeError(f"Groq API error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"]