import pandas as pd
from flask import Blueprint, jsonify, request

from services.model_service import predict_stat_threshold
from services.retrieval_service import build_player_context
from services.prompt_service import build_explanation_prompt
from services.llm_service import generate_explanation_with_hf
from services.template_service import template_explain
import traceback
explain_bp = Blueprint("explain", __name__)


def safe_float(value, default: float = 0.0) -> float:
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


@explain_bp.post("/explain")
def explain():
    payload = request.get_json(silent=True) or {}

    player_name = payload.get("player_name", "").strip()
    stat = payload.get("stat", "points").strip().lower()
    threshold = payload.get("threshold")
    model_type = payload.get("model_type", "baseline").strip().lower()

    game_id = payload.get("game_id")
    game_date = payload.get("game_date")
    team_abbr = payload.get("team_abbr")
    opponent_abbr = payload.get("opponent_abbr")

    if not player_name:
        return jsonify({"error": "player_name is required"}), 400

    if threshold is None:
        return jsonify({"error": "threshold is required"}), 400

    try:
        threshold = safe_float(threshold)
    except (TypeError, ValueError):
        return jsonify({"error": "threshold must be numeric"}), 400

    if model_type not in {"baseline", "enriched"}:
        return jsonify({"error": "model_type must be 'baseline' or 'enriched'"}), 400

    try:
        prediction_result = predict_stat_threshold(
            player_name=player_name,
            stat=stat,
            threshold=threshold,
            model_type=model_type,
        )

        predicted_value = prediction_result.get("predicted_value")
        probability = prediction_result.get("probability_over_threshold")

        context = build_player_context(
            player_name=player_name,
            stat=stat,
            threshold=threshold,
            predicted_value=predicted_value,
            probability=probability,
            game_id=game_id,
            game_date=game_date,
            team_abbr=team_abbr,
            opponent_abbr=opponent_abbr,
        )

        try:
            prompt = build_explanation_prompt(context)
            explanation = generate_explanation_with_hf(prompt)
            explanation_type = "llm"
        except Exception as llm_exc:
            print("LLM failed, falling back to template")
            print("Exception type:", type(llm_exc).__name__)
            print("Exception repr:", repr(llm_exc))
            traceback.print_exc()

            explanation = template_explain(context)
            explanation_type = "template"

        return jsonify({
            "player_name": player_name,
            "stat": stat,
            "threshold": threshold,
            "predicted_value": predicted_value,
            "probability_over_threshold": probability,
            "model_type": model_type,
            "explanation": explanation,
            "explanation_type": explanation_type,
            "context": context,
        })

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        import traceback
        print("EXPLANATION ROUTE FAILED")
        print("Exception type:", type(exc).__name__)
        print("Exception repr:", repr(exc))
        traceback.print_exc()
        return jsonify({"error": f"Explanation failed: {exc}"}), 500