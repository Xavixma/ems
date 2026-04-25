import logging
import aiomqtt

logger = logging.getLogger(__name__)


class MqttPublisher:
    def __init__(self, settings):
        self._settings = settings

    async def _publish_many(self, messages: list[tuple[str, str]]) -> None:
        try:
            async with aiomqtt.Client(
                hostname=self._settings.mqtt_host,
                port=self._settings.mqtt_port,
                username=self._settings.mqtt_username,
                password=self._settings.mqtt_password,
            ) as client:
                for topic, payload in messages:
                    await client.publish(topic, payload=payload, retain=True)
        except Exception as exc:
            logger.warning("MQTT publish failed: %s", exc)

    async def publish_solar(self, data: dict) -> None:
        await self._publish_many([
            ("ems/solar/power", str(data.get("dc_power", 0))),
            ("ems/solar/today", str(data.get("today_production", 0))),
            ("ems/solar/status", data.get("status", "offline")),
        ])

    async def publish_wallbox(self, data: dict) -> None:
        await self._publish_many([
            ("ems/wallbox/status", str(data.get("status", "unknown"))),
            ("ems/wallbox/power", str(data.get("charging_power", 0))),
            ("ems/wallbox/current_limit", str(data.get("max_charging_current", 0))),
        ])

    async def publish_ems_mode(self, mode) -> None:
        await self._publish_many([("ems/ems/mode", str(mode))])

    async def publish_ems_action(self, action: str | None) -> None:
        await self._publish_many([("ems/ems/action", action or "")])
