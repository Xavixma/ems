from fastapi import Request
from integrations.solar.hoymiles import HoymilesClient
from integrations.wallbox.pulsar import WallboxClient
from core.energy_manager import EnergyManager
from core.influx_writer import InfluxWriter


def get_solar_client(request: Request) -> HoymilesClient:
    return request.app.state.solar_client


def get_wallbox_client(request: Request) -> WallboxClient:
    return request.app.state.wallbox_client


def get_energy_manager(request: Request) -> EnergyManager:
    return request.app.state.energy_manager


def get_influx_writer(request: Request) -> InfluxWriter:
    return request.app.state.influx_writer
