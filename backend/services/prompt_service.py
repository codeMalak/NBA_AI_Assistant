def _fmt(value, default="N/A"):
    if value is None:
        return default
    return value


def build_explanation_prompt(context):
    playoff_note = ""
    if context.get("is_playoff_game") is True:
        playoff_note = (
            "This is a playoff game. Consider that star players often play heavier minutes, "
            "usage can increase, rotations tighten, and intensity is usually higher than in regular-season games.\n"
        )
    elif context.get("is_playoff_game") is False:
        playoff_note = "This is a regular-season game.\n"

    matchup_section = f"""
Matchup Context:
- Team: {_fmt(context.get("team_abbr"))}
- Opponent: {_fmt(context.get("opponent_abbr"))}
- Home/Away: {_fmt(context.get("home_away"))}
- Player height: {_fmt(context.get("player_height"))}
- Expected primary defender: {_fmt(context.get("primary_defender"))}
- Defender height: {_fmt(context.get("primary_defender_height"))}
- Height difference: {_fmt(context.get("height_difference"))}
- Opponent points allowed last 5: {_fmt(context.get("opponent_points_allowed_last_5"))}
- Opponent points allowed season: {_fmt(context.get("opponent_points_allowed_season"))}
- Opponent pace: {_fmt(context.get("opponent_pace"))}
- Opponent defensive rating: {_fmt(context.get("opponent_def_rating"))}
"""

    historical_section = f"""
Player Performance Context:
- Recent game values: {", ".join(map(str, context.get("recent_values", []))) if context.get("recent_values") else "N/A"}
- Last 5 average: {_fmt(context.get("last_5_avg"))}
- Last 10 average: {_fmt(context.get("last_10_avg"))}
- Season average: {_fmt(context.get("season_avg"))}
- Home split average: {_fmt(context.get("home_split_avg"))}
- Away split average: {_fmt(context.get("away_split_avg"))}
- Days rest: {_fmt(context.get("days_rest"))}
- Minutes last 5: {_fmt(context.get("minutes_last_5"))}
- Usage trend: {_fmt(context.get("usage_trend"))}
- Injury impact on team: {_fmt(context.get("team_injury_count"))}
- Injury impact on opponent: {_fmt(context.get("opponent_injury_count"))}
"""

    opponent_history_section = f"""
Opponent / Defender History:
- Average vs this team: {_fmt(context.get("vs_team_points_avg"))}
- Last 5 vs this team: {_fmt(context.get("vs_team_points_last_5"))}
- Career average vs this team: {_fmt(context.get("career_vs_team_avg"))}
- Average vs likely defender: {_fmt(context.get("vs_defender_avg"))}
- Last 5 vs likely defender: {_fmt(context.get("vs_defender_last_5"))}
"""

    playoff_section = f"""
Playoff Context:
- Is playoff game: {_fmt(context.get("is_playoff_game"))}
- Career playoff average: {_fmt(context.get("career_playoff_avg"))}
- Last playoff average: {_fmt(context.get("recent_playoff_avg"))}
- Playoff minutes average: {_fmt(context.get("playoff_minutes_avg"))}
"""

    prediction_section = f"""
Prediction:
- Player: {context["player_name"]}
- Statistic: {context["stat"]}
- Threshold: {context["threshold"]}
- Predicted value: {context["predicted_value"]}
- Probability of exceeding threshold: {context["probability_percent"]}%
"""

    lineup_injury_section = f"""
    Lineup and Injury Context:
    - Starter flag: {_fmt(context.get("starter_flag"))}
    - Bench flag: {_fmt(context.get("bench_flag"))}
    - Team injured count: {_fmt(context.get("team_injured_count"))}
    - Team starter-level injuries: {_fmt(context.get("team_starter_injured_count"))}
    - Estimated team minutes lost to injuries: {_fmt(context.get("team_injured_minutes_lost"))}
    - Estimated team points lost to injuries: {_fmt(context.get("team_injured_points_lost"))}
    - Opponent injured count: {_fmt(context.get("opponent_injured_count"))}
    - Opponent starter-level injuries: {_fmt(context.get("opponent_starter_injured_count"))}
    - Role boost flag: {_fmt(context.get("role_boost_flag"))}
    - Role boost score: {_fmt(context.get("role_boost_score"))}
    """

    return f"""
You are an NBA analytics assistant.

Your job is to explain whether this prediction is reasonable using ONLY the facts provided below.

Rules:
- If a player is starting while a starter-level teammate is injured, explain that his role, minutes, and shot opportunities may increase.
- If key opponent players are injured, explain how that may weaken defensive resistance or change pace.
- Do not claim a specific player is injured unless the injury data explicitly says so.
- Treat injury impact as an opportunity signal, not a guarantee.
- Do not explain your reasoning step by step.
- Do not say "I need to", "Let me", "First", or "step by step".
- Do not repeat raw stats already shown in the UI.
- Give only the final user-facing explanation.
- Keep the answer to exactly 4 complete sentences.
- Each sentence must be concise.
- Do not invent injuries, rankings, defenders, matchups, or statistics.
- If some context is missing, do not guess. Simply rely on the available facts.
- Pay special attention to recent performance, matchup difficulty, home/away context, playoff intensity, and opponent-specific history.
- If playoff context is available, mention how playoff basketball can differ from regular season basketball.
- If matchup size or defender context is available, mention whether the player may have a size advantage or disadvantage.
- If averages against the opponent or defender are available, use them.
- Be analytical, grounded, and concise.
- Write 5 to 8 sentences in plain English.
- End with a clear overall judgment about why the player is more likely or less likely to go over the threshold.

{playoff_note}

{prediction_section}

{historical_section}

{matchup_section}

{opponent_history_section}

{playoff_section}

Write the final explanation only. Do not include internal reasoning. Keep it to exactly 4 complete sentences.
""".strip()