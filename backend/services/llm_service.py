from __future__ import annotations

import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

HF_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HF_TOKEN")

# Pick one provider-backed model string from HF supported models.
HF_MODEL = "google/gemma-4-31B-it:novita"

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)


def generate_explanation_with_hf(prompt: str) -> str:
    if not HF_TOKEN:
        raise ValueError("HF_API_TOKEN or HF_TOKEN is missing from .env")

    completion = client.chat.completions.create(
        model=HF_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an NBA analytics assistant. "
                    "Use only the provided facts. "
                    "Do not invent injuries, rankings, matchup details, or statistics."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        max_tokens=180,
        temperature=0.7,
    )

    message = completion.choices[0].message.content
    if not message or not isinstance(message, str):
        raise ValueError(f"Unexpected Hugging Face response: {completion}")

    return message.strip()