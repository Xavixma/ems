import logging
from datetime import datetime, timedelta
from enum import Enum
from math import floor

logger = logging.getLogger(__name__)


class EmsMode(str, Enum):
    MANUAL = "manual"
    AUTO = "auto"
    ECO = "eco"


class EnergyManager:
    def __init__(self, settings, solar_client, wallbox_client, mqtt_publisher, influx_writer):
        self._settings = settings
        self._solar = solar_client
        self._wallbox = wallbox_client
        self._mqtt = mqtt_publisher
        self._influx = influx_writer

        self._mode = EmsMode(settings.ems_default_mode)
        self._last_action: str | None = None
        self._last_action_ts: datetime | None = None
        self._charging_active = False

    @property
    def mode(self) -> EmsMode:
        return self._mode

    @property
    def last_action(self) -> str | None:
        return self._last_action

    @property
    def last_action_ts(self) -> datetime | None:
        return self._last_action_ts

    def set_mode(self, mode: EmsMode) -> None:
        self._mode = mode
        logger.info("EMS mode changed to %s", mode)

    def _hysteresis_ok(self) -> bool:
        if self._last_action_ts is None:
            return True
        elapsed = datetime.now() - self._last_action_ts
        return elapsed > timedelta(minutes=self._settings.ems_histeresi_minuts)

    async def _record_action(self, action: str) -> None:
        self._last_action = action
        self._last_action_ts = datetime.now()
        logger.info("EMS action: %s", action)
        await self._influx.write_ems_event(str(self._mode), action)

    async def tick(self) -> None:
        solar_data = await self._solar.get_production()
        wallbox_data = await self._wallbox.get_status()

        await self._mqtt.publish_solar(solar_data)
        await self._mqtt.publish_wallbox(wallbox_data)
        await self._mqtt.publish_ems_mode(self._mode)

        await self._influx.write_solar(solar_data)
        await self._influx.write_wallbox(wallbox_data)

        dc_power = solar_data["dc_power"]
        wallbox_power = wallbox_data.get("charging_power", 0)
        surplus = dc_power - wallbox_power

        match self._mode:
            case EmsMode.MANUAL:
                pass
            case EmsMode.AUTO:
                await self._run_auto(surplus)
            case EmsMode.ECO:
                await self._run_eco(surplus)

    async def _run_auto(self, surplus: float) -> None:
        threshold_on = self._settings.ems_threshold_on_w
        threshold_off = self._settings.ems_threshold_off_w

        if surplus > threshold_on and not self._charging_active:
            if self._hysteresis_ok():
                await self._wallbox.set_current_limit(6)
                await self._wallbox.start_charging()
                self._charging_active = True
                await self._record_action("start_charging")
                await self._mqtt.publish_ems_action(self._last_action)

        elif surplus < threshold_off and self._charging_active:
            if self._hysteresis_ok():
                await self._wallbox.stop_charging()
                self._charging_active = False
                await self._record_action("stop_charging")
                await self._mqtt.publish_ems_action(self._last_action)

    async def _run_eco(self, surplus: float) -> None:
        voltage = self._settings.ems_voltage
        phases = self._settings.ems_phases
        target_amps = max(6, min(32, floor(surplus / voltage / phases)))

        await self._wallbox.set_current_limit(target_amps)
        await self._record_action(f"set_current_{target_amps}A")
        await self._mqtt.publish_ems_action(self._last_action)
