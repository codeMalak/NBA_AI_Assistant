from __future__ import annotations

import os
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

load_dotenv()

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_MODEL = "Qwen/Qwen2.5-7B-Instruct"

client = InferenceClient(
    provider="hf-inference",
    api_key=HF_API_TOKEN,
)


def generate_explanation_with_hf(prompt: str) -> str:
    if not HF_API_TOKEN:
        raise ValueError("HF_API_TOKEN is missing from .env")

    try:
        result = client.text_generation(
            prompt,
            model=HF_MODEL,
            max_new_tokens=180,
            temperature=0.7,
        )

        if isinstance(result, str) and result.strip():
            return result.strip()

        raise ValueError(f"Unexpected text_generation response: {result}")

    except Exception as first_error:
        try:
            completion = client.chat.completions.create(
                model=HF_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an NBA analytics assistant. "
                            "Use only the provided facts. "
                            "Do not invent stats, injuries, or matchups."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=180,
                temperature=0.7,
            )

            message = completion.choices[0].message.content
            if isinstance(message, str) and message.strip():
                return message.strip()

            raise ValueError(f"Unexpected chat completion response: {completion}")

        except Exception as second_error:
            raise ValueError(
                f"Hugging Face inference failed. "
                f"text_generation error: {first_error}; "
                f"chat_completion error: {second_error}"
            )