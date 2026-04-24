import pandas as pd


def safe_float(value, default=0.0):
    if pd.isna(value):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def template_explain(context):
    player = context.get("player_name", "This player")
    stat = context.get("stat", "points")
    threshold = safe_float(context.get("threshold"))
    predicted = safe_float(context.get("predicted_value"))
    probability = safe_float(context.get("probability_percent"))
    last_5 = safe_float(context.get("last_5_avg"))
    season = safe_float(context.get("season_avg"))
    opponent = context.get("opponent_abbr") or "the opponent"

    return (
        f"{player} is projected for {predicted:.2f} {stat} against {opponent}, "
        f"with about a {probability:.1f}% chance to clear {threshold:.1f}. "
        f"His recent form is around {last_5:.1f} {stat} over the last five games, "
        f"compared with a season average of {season:.1f}. "
        f"Based on the available context, the projection is a reasonable estimate, "
        f"but missing matchup or lineup details may limit confidence."
    )