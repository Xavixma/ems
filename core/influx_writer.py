import logging
from datetime import date, datetime, timezone

from influxdb_client import Point
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync

logger = logging.getLogger(__name__)


class InfluxWriter:
    def __init__(self, settings):
        self._bucket = settings.influxdb_bucket
        self._client = InfluxDBClientAsync(
            url=settings.influxdb_url,
            token=settings.influxdb_token,
            org=settings.influxdb_org,
        )
        self._write_api = self._client.write_api()
        self._query_api = self._client.query_api()

    async def write_solar(self, data: dict) -> None:
        point = (
            Point("solar")
            .tag("status", data.get("status", "unknown"))
            .field("dc_power", float(data["dc_power"]))
            .field("today_production", float(data["today_production"]))
            .field("total_production", float(data["total_production"]))
        )
        try:
            await self._write_api.write(bucket=self._bucket, record=point)
        except Exception as e:
            logger.warning("InfluxDB write_solar failed: %s", e)

    async def write_wallbox(self, data: dict) -> None:
        point = (
            Point("wallbox")
            .tag("status", str(data.get("status", "unknown")))
            .tag("locked", str(data.get("locked", False)))
            .field("charging_power", float(data.get("charging_power", 0)))
            .field("max_charging_current", float(data.get("max_charging_current", 0)))
            .field("session_energy", float(data.get("session_energy", 0)))
        )
        try:
            await self._write_api.write(bucket=self._bucket, record=point)
        except Exception as e:
            logger.warning("InfluxDB write_wallbox failed: %s", e)

    async def write_ems_event(self, mode: str, action: str) -> None:
        point = (
            Point("ems_event")
            .tag("mode", mode)
            .field("action", action)
        )
        try:
            await self._write_api.write(bucket=self._bucket, record=point)
        except Exception as e:
            logger.warning("InfluxDB write_ems_event failed: %s", e)

    async def query_solar_hourly_avg(self) -> list[dict]:
        today = date.today()
        start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        query = f"""
from(bucket: "{self._bucket}")
  |> range(start: {start}, stop: now())
  |> filter(fn: (r) => r._measurement == "solar" and r._field == "dc_power")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: true)
  |> fill(value: 0.0)
"""
        rows: dict[int, float] = {}
        try:
            tables = await self._query_api.query(query)
            for table in tables:
                for record in table.records:
                    # aggregateWindow sets _time to the end of the window, so hour 1 = 00:00–01:00
                    hour = (record.get_time().hour - 1) % 24
                    rows[hour] = record.get_value() or 0.0
        except Exception as e:
            logger.warning("InfluxDB query_solar_hourly_avg failed: %s", e)

        return [
            {"hour": h, "avg_kw": round(rows.get(h, 0.0) / 1000.0, 3)}
            for h in range(24)
        ]

    async def close(self) -> None:
        await self._client.close()
