from pydantic import BaseModel


class SolarProduction(BaseModel):
    dc_power: float       # W
    today_production: float  # kWh
    total_production: float  # kWh
    status: str           # online / offline


class SolarStats(BaseModel):
    today_production: float  # kWh
    total_production: float  # kWh
