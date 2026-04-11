def build_explanation_prompt(context):
    player_name = context["player_name"]
    stat = context["stat"]
    threshold = context["threshold"]
    predicted_value = context["predicted_value"]
    probability_percent = context["probability_percent"]
    last_5_avg = context["last_5_avg"]
    season_avg = context["season_avg"]
    recent_values = ", ".join(map(str, context["recent_values"]))

    return f"""
You are an NBA analytics assistant.

Use only the facts provided below.
Do not invent injuries, matchups, rankings, or statistics that are not listed.
Write a short explanation in plain English in 4 to 6 sentences.
Do not mention that you are an AI model.
Keep the response focused on why the prediction is reasonable.

Player: {player_name}
Statistic: {stat}
Threshold: {threshold}
Predicted value: {predicted_value}
Probability of exceeding threshold: {probability_percent}%
Last 5 game average: {last_5_avg}
Season average: {season_avg}
Recent game values: {recent_values}

Explain why this prediction is reasonable.
""".strip()