from fastapi import APIRouter, Depends
from api.dependencies import get_energy_manager
from api.schemas.ems import ModeRequest
from core.energy_manager import EnergyManager

router = APIRouter(prefix="/ems", tags=["ems"])


@router.get("/status")
async def get_status(em: EnergyManager = Depends(get_energy_manager)):
    return {
        "mode": em.mode,
        "last_action": em.last_action,
        "last_action_ts": em.last_action_ts,
    }


@router.put("/mode")
async def set_mode(body: ModeRequest, em: EnergyManager = Depends(get_energy_manager)):
    em.set_mode(body.mode)
    return {"ok": True, "mode": body.mode}
