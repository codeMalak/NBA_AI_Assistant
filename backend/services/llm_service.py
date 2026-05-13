from __future__ import annotations
import re
import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

HF_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HF_TOKEN")
HF_MODEL = "HuggingFaceH4/zephyr-7b-beta"


def _build_user_prompt(prompt: str) -> str:
    return (
        "You are an NBA analytics assistant.\n"
        "Use only the provided facts.\n"
        "Do not invent injuries, rankings, matchup details, or statistics.\n\n"
        f"{prompt}"
    )


def generate_explanation_with_hf(prompt: str) -> str:
    if not HF_TOKEN:
        raise ValueError("HF_API_TOKEN or HF_TOKEN is missing from .env")

    client = InferenceClient(token=HF_TOKEN)

    completion = client.chat.completions.create(
        model=HF_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=260,
        temperature=0.2,
    )

    message_obj = completion.choices[0].message
    content = getattr(message_obj, "content", None)

    if not content or not isinstance(content, str):
        raise RuntimeError(
            f"LLM did not return final content for model '{HF_MODEL}'."
        )

    return clean_explanation(content)


import re


def clean_explanation(text: str) -> str:
    if not text:
        return ""

    cleaned = text.strip()

    # Remove fake user turns or chat-template artifacts
    stop_markers = [
        "[USER]",
        "[INST]",
        "[/INST]",
        "<|user|>",
        "User:",
        "USER:",
        "\nUser:",
        "\nUSER:",
    ]

    for marker in stop_markers:
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0].strip()

    # Remove assistant labels
    for marker in ["[ASST]", "Assistant:", "ASSISTANT:", "<|assistant|>"]:
        cleaned = cleaned.replace(marker, "").strip()

    # If the model repeats another answer, keep only the first one
    first_decision = cleaned.find("Decision:")
    if first_decision != -1:
        second_decision = cleaned.find("Decision:", first_decision + len("Decision:"))
        if second_decision != -1:
            cleaned = cleaned[:second_decision].strip()

    # Normalize weird spacing around decimals: 22. 24 -> 22.24
    cleaned = re.sub(r"(\d+)\.\s+(\d+)", r"\1.\2", cleaned)

    return cleaned.strip()