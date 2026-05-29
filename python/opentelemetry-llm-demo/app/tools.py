from agents import function_tool


@function_tool
def calculate_win_percentage(wins: int, losses: int) -> str:
    """Calculates the winning percentage for an NBA team given their wins and losses."""

    total_games = wins + losses
    if total_games == 0:
        return ".000"

    return f"{wins / total_games:.3f}".lstrip("0")
