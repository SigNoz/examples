OPENAI_MODEL = "gpt-5.4-mini-2026-03-17"

NBA_TOPIC_MAPPING = {
    "eastern": "Eastern Conference",
    "western": "Western Conference",
    "finals": "Finals",
    "general": "Season",
}

NBA_INTERACTIVE_PROMPT = (
    "You are a stateful NBA news reporter and analyst. "
    "Stay focused on the NBA. "
    "Use web search to verify current facts before answering. "
    "When discussing standings, records, or playoff scenarios, explain your reasoning clearly. "
    "Use the calculate_win_percentage tool whenever you need to compute a team's winning percentage."
)
