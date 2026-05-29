import datetime as dt


def build_nba_turn_prompt(nba_topic: str, user_message: str | None) -> str:
    if user_message:
        return user_message

    # fallback to general news if no prompt was provided
    return (
        f"What is the latest news and analysis for NBA {nba_topic}, "
        f"as of {dt.date.today()}?"
    )
