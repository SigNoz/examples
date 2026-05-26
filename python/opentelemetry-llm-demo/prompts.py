import datetime as dt


def build_nba_analysis_prompt(nba_topic: str) -> str:
    return f"What is the latest news and analysis for NBA {nba_topic}, as of {dt.date.today()}?"
