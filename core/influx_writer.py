import logging
from datetime import date, datetime, timezone

import httpx

logger = logging.getLogger(__name__)


def _line(measurement: str, tags: dict[str, str], fields: dict) -> str:
    tag_str = ",".join(f"{k}={v}" for k, v in tags.items())
    parts = []
    for k, v in fields.items():
        if isinstance(v, str):
            parts.append(f'{k}="{v}"')
        else:
            parts.append(f"{k}={float(v)}")
    field_str = ",".join(parts)
    return f"{measurement},{tag_str} {field_str}" if tag_str else f"{measurement} {field_str}"


class InfluxWriter:
    def __init__(self, settings):
        self._db = settings.influxdb_database
        base_url = f"http://{settings.influxdb_host}:{settings.influxdb_port}"
        auth = (settings.influxdb_username, settings.influxdb_password) if settings.influxdb_username else None
        self._client = httpx.AsyncClient(base_url=base_url, auth=auth, timeout=10.0)

    async def ensure_database(self) -> None:
        try:
            resp = await self._client.post(
                "/query",
                content=f'q=CREATE DATABASE "{self._db}"',
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            resp.raise_for_status()
            logger.info("InfluxDB database '%s' ready", self._db)
        except Exception as e:
            logger.warning("InfluxDB ensure_database failed: %s", e)

    async def _write(self, line: str) -> None:
        try:
            resp = await self._client.post(
                f"/write?db={self._db}&precision=s",
                content=line,
                headers={"Content-Type": "application/octet-stream"},
            )
            resp.raise_for_status()
        except Exception as e:
            logger.warning("InfluxDB write failed: %s", e)

    async def write_solar(self, data: dict) -> None:
        await self._write(_line(
            "solar",
            {"status": data.get("status", "unknown")},
            {
                "dc_power": data["dc_power"],
                "today_production": data["today_production"],
                "total_production": data["total_production"],
            },
        ))

    async def write_wallbox(self, data: dict) -> None:
        await self._write(_line(
            "wallbox",
            {
                "status": str(data.get("status", "unknown")),
                "locked": str(data.get("locked", False)).lower(),
            },
            {
                "charging_power": data.get("charging_power", 0),
                "max_charging_current": data.get("max_charging_current", 0),
                "session_energy": data.get("session_energy", 0),
            },
        ))

    async def write_ems_event(self, mode: str, action: str) -> None:
        await self._write(_line("ems_event", {"mode": mode}, {"action": action}))

    async def query_solar_hourly_avg(self, for_date: date | None = None) -> list[dict]:
        target = for_date or date.today()
        start = datetime(target.year, target.month, target.day, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        if target < date.today():
            stop = datetime(target.year, target.month, target.day, 23, 59, 59, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        else:
            stop = "now()"

        q = (
            f'SELECT mean("dc_power") FROM "solar" '
            f"WHERE time >= '{start}' AND time < {stop} "
            f"GROUP BY time(1h) fill(0)"
        )

        rows: dict[int, float] = {}
        try:
            resp = await self._client.get("/query", params={"db": self._db, "q": q, "epoch": "s"})
            resp.raise_for_status()
            series = resp.json()["results"][0].get("series", [])
            for serie in series:
                for ts, val in serie["values"]:
                    hour = int(ts) % 86400 // 3600
                    rows[hour] = val or 0.0
        except Exception as e:
            logger.warning("InfluxDB query_solar_hourly_avg failed: %s", e)

        return [{"hour": h, "avg_kw": round(rows.get(h, 0.0) / 1000.0, 3)} for h in range(24)]

    async def close(self) -> None:
        await self._client.aclose()
