import datetime as dt


def build_nba_analysis_prompt(nba_topic: str) -> str:
    return f"What is the latest news and analysis for NBA {nba_topic}, as of {dt.date.today()}?"


def build_nba_report_prompt(nba_topic: str) -> str:
    return f"Please prepare a detailed markdown report on the current state of affairs, standings, and news for NBA {nba_topic}. Ensure it has distinct sections: Summary, Key Standings/Developments, and Outlook."
