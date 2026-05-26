OPENAI_MODEL = "gpt-5.4-mini-2026-03-17"

NBA_REPORTER_PROMPT = (
    "You're an NBA news reporter that gives the user the latest news and analysis on the NBA."
)

NBA_SYSTEM_PROMPT = (
    NBA_REPORTER_PROMPT
    + " Use web search to verify current facts before answering questions about recent news, "
    + "standings, or playoff state."
)

NBA_TOPIC_MAPPING = {
    "eastern": "Eastern Conference",
    "western": "Western Conference",
    "finals": "Finals",
    "general": "Season",
}
