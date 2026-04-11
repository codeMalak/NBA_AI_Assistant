def template_explain(context):
    player_name = context["player_name"]
    stat = context["stat"]
    threshold = context["threshold"]
    predicted_value = context["predicted_value"]
    probability_percent = context["probability_percent"]
    last_5_avg = context["last_5_avg"]
    season_avg = context["season_avg"]
    recent_values = context["recent_values"]

    return (
        f"{player_name} has an estimated {probability_percent:.0f}% chance of exceeding "
        f"{threshold:.1f} {stat}. The model projects about {predicted_value:.2f} {stat} "
        f"based on recent performance. Over the last five games, the player has averaged "
        f"{last_5_avg:.2f} {stat}, compared with a season average of {season_avg:.2f}. "
        f"Recent game values were {', '.join(map(str, recent_values))}."
    )