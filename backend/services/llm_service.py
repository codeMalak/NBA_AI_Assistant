from __future__ import annotations

import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

HF_TOKEN = os.getenv("HF_API_TOKEN") or os.getenv("HF_TOKEN")
HF_MODEL = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"


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

    client = InferenceClient(
        token=HF_TOKEN,
        provider="auto",
    )

    user_prompt = _build_user_prompt(prompt)

    try:
        completion = client.chat.completions.create(
            model=HF_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt,
                }
            ],
            max_tokens=180,
            temperature=0.6,
        )
    except Exception as exc:
        raise RuntimeError(
            f"Hugging Face chat completion failed for model '{HF_MODEL}': {repr(exc)}"
        ) from exc

    try:
        message_obj = completion.choices[0].message
    except Exception as exc:
        raise RuntimeError(
            f"Unexpected Hugging Face response structure for model '{HF_MODEL}': {repr(completion)}"
        ) from exc

    content = getattr(message_obj, "content", None)
    reasoning_content = getattr(message_obj, "reasoning_content", None)

    final_text = content or reasoning_content

    if not final_text or not isinstance(final_text, str):
        raise RuntimeError(
            f"Empty or invalid LLM message returned for model '{HF_MODEL}': {repr(completion)}"
        )

    return final_text.strip()