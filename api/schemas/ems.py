from pydantic import BaseModel
from core.energy_manager import EmsMode


class ModeRequest(BaseModel):
    mode: EmsMode
