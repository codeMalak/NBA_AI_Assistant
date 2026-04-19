from flask import Blueprint, jsonify, request

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

chatbot_bp = Blueprint("chatbot", __name__)


@chatbot_bp.post("/chatbot")
def chat():
    try:
        data = request.get_json()

        if not data or "messages" not in data:
            return jsonify({"error": "Missing 'messages' in request body"})

        messages = data["messages"]

        completion = client.chat.completions.create(
            model=HF_MODEL,
            messages=messages,
            max_tokens=400,
            temperature=0.7,
        )

        reply = completion.choices[0].message.content

        return jsonify({"reply": reply})

    except Exception as error:
        return jsonify({"error": "Chat request failed", "details": str(error)}), 500
