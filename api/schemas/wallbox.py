from pydantic import BaseModel, Field


class CurrentLimitRequest(BaseModel):
    amps: int = Field(..., ge=6, le=32, description="Charging current in Amperes (6–32A)")
