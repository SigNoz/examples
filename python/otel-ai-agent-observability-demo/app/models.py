from pydantic import BaseModel, Field


class AgentTurnRequest(BaseModel):
    topic: str = Field(
        description="NBA topic slug: eastern, western, finals, or general."
    )
    message: str | None = Field(
        default=None,
        description="User instruction for this turn. If omitted, the app generates a topic overview.",
    )
    session_id: str | None = Field(
        default=None,
        description="existing OpenAI conversation ID to continue an NBA chat. omit it to start a new one.",
    )


class AgentTurnResponse(BaseModel):
    topic: str
    session_id: str | None = None
    message: str
    model: str
    usage: dict[str, int] | None = None
