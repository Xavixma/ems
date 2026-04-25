from fastapi import APIRouter, Depends
from api.dependencies import get_wallbox_client
from api.models.wallbox import WallboxStatus
from api.schemas.wallbox import CurrentLimitRequest
from integrations.wallbox.pulsar import WallboxClient

router = APIRouter(prefix="/wallbox", tags=["wallbox"])


@router.get("/status", response_model=WallboxStatus)
async def get_status(client: WallboxClient = Depends(get_wallbox_client)):
    data = await client.get_status()
    return WallboxStatus(**data)


@router.post("/start")
async def start_charging(client: WallboxClient = Depends(get_wallbox_client)):
    await client.start_charging()
    return {"ok": True}


@router.post("/stop")
async def stop_charging(client: WallboxClient = Depends(get_wallbox_client)):
    await client.stop_charging()
    return {"ok": True}


@router.put("/current-limit")
async def set_current_limit(
    body: CurrentLimitRequest,
    client: WallboxClient = Depends(get_wallbox_client),
):
    await client.set_current_limit(body.amps)
    return {"ok": True, "amps": body.amps}
