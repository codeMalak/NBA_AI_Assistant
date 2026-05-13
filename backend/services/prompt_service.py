def _fmt(value, default="N/A"):
    if value is None or value == "":
        return default
    return value


def build_explanation_prompt(context):
    probability = float(context.get("probability_percent", 0))
    decision = "YES" if probability >= 50 else "NO"

    return f"""
You are an NBA analytics assistant.

Your job is to explain a player points prediction using the model output and the provided context.

Required output format:
Decision: {decision}
Explanation: Write 4 to 5 complete sentences explaining WHY this is a {decision} decision.

Rules:
- Do not repeat the decision more than once.
- Do not generate a second answer.
- Do not include [USER], [ASST], User:, or Assistant:.
- Do not write internal reasoning or step-by-step thoughts.
- Do not list raw recent game scores.
- Use the model prediction and probability as the source of truth.
- If the decision is YES, explain the strongest reasons supporting the over.
- If the decision is NO, explain why the context is not strong enough to support the over.
- Mention relevant context such as recent form, season average, home/away, opponent, starter role, injuries, or role boost when available.
- If a context field is N/A, ignore it.
- Keep the explanation specific and useful.

Model Output:
- Player: {context["player_name"]}
- Stat: {context["stat"]}
- Threshold: {context["threshold"]}
- Predicted value: {context["predicted_value"]}
- Probability over threshold: {context["probability_percent"]}%

Player Context:
- Last 5 average: {_fmt(context.get("last_5_avg"))}
- Last 10 average: {_fmt(context.get("last_10_avg"))}
- Season average: {_fmt(context.get("season_avg"))}
- Home/Away: {_fmt(context.get("home_away"))}
- Home split average: {_fmt(context.get("home_split_avg"))}
- Away split average: {_fmt(context.get("away_split_avg"))}
- Minutes last 5: {_fmt(context.get("minutes_last_5"))}
- Usage trend: {_fmt(context.get("usage_trend"))}

Matchup Context:
- Team: {_fmt(context.get("team_abbr"))}
- Opponent: {_fmt(context.get("opponent_abbr"))}
- Opponent pace: {_fmt(context.get("opponent_pace"))}
- Opponent defensive rating: {_fmt(context.get("opponent_def_rating"))}
- Average vs this team: {_fmt(context.get("vs_team_points_avg"))}

Lineup/Injury Context:
- Starter flag: {_fmt(context.get("starter_flag"))}
- Team starter-level injuries: {_fmt(context.get("team_starter_injured_count"))}
- Team injury minutes lost: {_fmt(context.get("team_injured_minutes_lost"))}
- Team injury points lost: {_fmt(context.get("team_injured_points_lost"))}
- Role boost flag: {_fmt(context.get("role_boost_flag"))}
- Role boost score: {_fmt(context.get("role_boost_score"))}

Return only one final answer.
""".strip()