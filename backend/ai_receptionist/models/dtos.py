from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    env: str = "local"


class TwilioWebhookResult(BaseModel):
    message: str
    provider: str = "twilio"
    from_: str | None = None
