import logging
from hoymiles_wifi.dtu import DTU

logger = logging.getLogger(__name__)


class HoymilesClient:
    def __init__(self, ip: str):
        self._dtu = DTU(host=ip)

    async def get_production(self) -> dict:
        try:
            response = await self._dtu.async_get_real_data_new()
            if response is None:
                raise ValueError("empty response")

            dc_power = float(response.dtu_power) / 10.0  # unit: 0.1 W
            today_production = response.dtu_daily_energy / 1000.0
            total_production = sum(pv.energy_total for pv in response.pv_data) / 1000.0

            return {
                "dc_power": dc_power,
                "today_production": today_production,
                "total_production": total_production,
                "status": "online",
            }
        except Exception as exc:
            logger.warning("Hoymiles read failed: %s", exc)
            return {
                "dc_power": 0.0,
                "today_production": 0.0,
                "total_production": 0.0,
                "status": "offline",
            }
