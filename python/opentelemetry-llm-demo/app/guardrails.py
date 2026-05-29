from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, input_guardrail


@input_guardrail()
def nba_content_guardrail(
    context: RunContextWrapper[None],
    agent: Agent,
    input_data: str | list,
) -> GuardrailFunctionOutput:
    """Ensures the user query is relevant to basketball/NBA."""

    del context, agent

    keywords = [
        "nba",
        "basketball",
        "player",
        "team",
        "finals",
        "playoff",
        "standing",
        "court",
        "wins",
        "losses",
        "score",
        "game",
        "championship",
        "conference",
        "mvp",
        "report",
        "news",
        "cavs",
        "knicks",
        "thunder",
        "spurs",
    ]

    if isinstance(input_data, list):
        latest_user_message = next(
            (
                item.get("content", "")
                for item in reversed(input_data)
                if isinstance(item, dict) and item.get("role") == "user"
            ),
            "",
        )
        input_query = latest_user_message
    else:
        input_query = input_data

    input_query = input_query.lower()
    is_relevant = any(keyword in input_query for keyword in keywords)

    if len(input_query) < 5 or is_relevant:
        return GuardrailFunctionOutput(tripwire_triggered=False, output_info=None)

    return GuardrailFunctionOutput(
        tripwire_triggered=True,
        output_info={
            "reason": "The request is off-topic. Please ask questions relevant to NBA or basketball."
        },
    )
