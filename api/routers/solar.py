from fastapi import APIRouter, Depends
from api.dependencies import get_solar_client, get_influx_writer
from api.models.solar import SolarProduction, SolarStats
from core.influx_writer import InfluxWriter
from integrations.solar.hoymiles import HoymilesClient

router = APIRouter(prefix="/solar", tags=["solar"])


@router.get("/production", response_model=SolarProduction)
async def get_production(client: HoymilesClient = Depends(get_solar_client)):
    data = await client.get_production()
    return SolarProduction(**data)


@router.get("/stats", response_model=SolarStats)
async def get_stats(client: HoymilesClient = Depends(get_solar_client)):
    data = await client.get_production()
    return SolarStats(
        today_production=data["today_production"],
        total_production=data["total_production"],
    )


@router.get("/history")
async def get_history(influx: InfluxWriter = Depends(get_influx_writer)):
    return await influx.query_solar_hourly_avg()
