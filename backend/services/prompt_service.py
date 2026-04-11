def build_explanation_prompt(context):
    return f"""
Use only the information below.
Do not invent injuries or statistics.
Write 4 to 6 plain-English sentences.

Player: {context["player_name"]}
Team: {context.get("team_abbr", "Unknown")}
Opponent: {context.get("opponent_abbr", "Unknown")}
Statistic: {context["stat"]}
Threshold: {context["threshold"]}
Predicted value: {context["predicted_value"]}
Probability of exceeding threshold: {context["probability_percent"]}%
Last 5 average: {context["last_5_avg"]}
Season average: {context["season_avg"]}
Recent game values: {", ".join(map(str, context["recent_values"]))}
Average vs this opponent: {context.get("vs_team_points_avg", "N/A")}
Last 5 vs this opponent: {context.get("vs_team_points_last_5", "N/A")}
Opponent points allowed last 5: {context.get("opponent_points_allowed_last_5", "N/A")}
Opponent points allowed season: {context.get("opponent_points_allowed_season", "N/A")}

Explain why this prediction is reasonable against this opponent.
""".strip()