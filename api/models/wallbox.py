from pydantic import BaseModel


class WallboxStatus(BaseModel):
    status: str
    charging_power: float  # W
    max_charging_current: int  # A
    session_energy: float  # kWh
    locked: bool
