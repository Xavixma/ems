import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.config import get_settings
from core.energy_manager import EnergyManager
from core.influx_writer import InfluxWriter
from core.mqtt_publisher import MqttPublisher
from core.scheduler import EmsScheduler
from integrations.solar.hoymiles import HoymilesClient
from integrations.wallbox.pulsar import WallboxClient
from api.routers import solar, wallbox, ems

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    solar_client = HoymilesClient(settings.hoymiles_dtu_ip)
    wallbox_client = WallboxClient(
        charger_id=settings.wallbox_charger_id,
        token=settings.wallbox_token,
        email=settings.wallbox_email,
        password=settings.wallbox_password,
    )
    mqtt_publisher = MqttPublisher(settings)
    influx_writer = InfluxWriter(settings)
    energy_manager = EnergyManager(settings, solar_client, wallbox_client, mqtt_publisher, influx_writer)
    scheduler = EmsScheduler(energy_manager, settings.ems_poll_interval_s)

    app.state.solar_client = solar_client
    app.state.wallbox_client = wallbox_client
    app.state.energy_manager = energy_manager
    app.state.influx_writer = influx_writer

    scheduler.start()
    logger.info("EMS started")

    yield

    scheduler.stop()
    await wallbox_client.close()
    await influx_writer.close()
    logger.info("EMS stopped")


app = FastAPI(
    title="EMS — Energy Management System",
    description="Sistema de gestió energètica per habitatge unifamiliar",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(solar.router)
app.include_router(wallbox.router)
app.include_router(ems.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}


# Mounted last so API routes take priority
app.mount("/", StaticFiles(directory="static", html=True), name="static")
