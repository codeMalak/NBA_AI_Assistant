from flask import Blueprint, jsonify, request

from services.model_service import predict_stat_threshold
from services.retrieval_service import build_player_context
from services.prompt_service import build_explanation_prompt
from services.llm_service import generate_explanation_with_hf
from services.template_service import template_explain

explain_bp = Blueprint("explain", __name__)


@explain_bp.post("/explain")
def explain():
    payload = request.get_json(silent=True) or {}
    player_name = payload.get("player_name", "").strip()
    stat = payload.get("stat", "points").strip().lower()
    threshold = payload.get("threshold")

    if not player_name:
        return jsonify({"error": "player_name is required"}), 400

    if threshold is None:
        return jsonify({"error": "threshold is required"}), 400

    try:
        threshold = float(threshold)
    except (TypeError, ValueError):
        return jsonify({"error": "threshold must be numeric"}), 400

    try:
        prediction_result = predict_stat_threshold(
            player_name=player_name,
            stat=stat,
            threshold=threshold
        )

        predicted_value = prediction_result.get("predicted_value")
        probability = prediction_result.get("probability_over_threshold")

        if predicted_value is None or probability is None:
            return jsonify({"error": "Prediction result missing required fields"}), 500

        context = build_player_context(
            player_name=player_name,
            stat=stat,
            threshold=threshold,
            predicted_value=predicted_value,
            probability=probability
        )

        if context is None:
            return jsonify({"error": f"No data found for player '{player_name}'"}), 404

        try:
            prompt = build_explanation_prompt(context)
            explanation = generate_explanation_with_hf(prompt)
            explanation_type = "llm"
        except Exception as llm_exc:
            print(f"LLM failed, falling back to template: {llm_exc}")
            explanation = template_explain(context)
            explanation_type = "template"

        return jsonify({
            "player_name": player_name,
            "stat": stat,
            "threshold": threshold,
            "predicted_value": predicted_value,
            "probability_over_threshold": probability,
            "explanation": explanation,
            "explanation_type": explanation_type,
            "context": context
        })

    except ValueError as exc:
        return jsonify({"error": str(exc)}), 404
    except Exception as exc:
        return jsonify({"error": f"Explanation failed: {exc}"}), 500