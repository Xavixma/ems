import base64
import logging
import httpx

logger = logging.getLogger(__name__)

_API_BASE = "https://api.wall-box.com"

# Remote action codes
_ACTION_START = 1
_ACTION_STOP = 2


class WallboxClient:
    def __init__(
        self,
        charger_id: str,
        token: str | None = None,
        email: str | None = None,
        password: str | None = None,
    ):
        if not token and not (email and password):
            raise ValueError("Provide either WALLBOX_TOKEN or WALLBOX_EMAIL + WALLBOX_PASSWORD")
        self._email = email
        self._password = password
        self._charger_id = charger_id
        self._token: str | None = token
        self._static_token = token is not None  # don't try to refresh a user-supplied token
        self._client = httpx.AsyncClient(timeout=10.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def _authenticate(self) -> str:
        credentials = base64.b64encode(f"{self._email}:{self._password}".encode()).decode()
        resp = await self._client.get(
            f"{_API_BASE}/auth/token/user",
            headers={"Authorization": f"Basic {credentials}", "Accept": "application/json"},
        )
        resp.raise_for_status()
        self._token = resp.json()["data"]["attributes"]["token"]
        return self._token

    async def _headers(self) -> dict:
        if self._token is None:
            await self._authenticate()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        headers = await self._headers()
        resp = await self._client.request(method, f"{_API_BASE}{path}", headers=headers, **kwargs)
        if resp.status_code == 401 and not self._static_token:
            # Token expired — re-authenticate once and retry
            self._token = None
            headers = await self._headers()
            resp = await self._client.request(method, f"{_API_BASE}{path}", headers=headers, **kwargs)
        resp.raise_for_status()
        return resp

    async def get_status(self) -> dict:
        resp = await self._request("GET", f"/v2/charger/{self._charger_id}/status")
        data = resp.json()
        return {
            "status": str(data.get("status_id", "unknown")),
            "charging_power": float(data.get("charging_power", 0)),
            "max_charging_current": int(data.get("max_charging_current", 0)),
            "session_energy": float(data.get("added_energy", 0)),
            "locked": bool(data.get("locked", False)),
        }

    async def start_charging(self) -> None:
        await self._request(
            "POST",
            f"/v2/charger/{self._charger_id}/remote-action",
            json={"action": _ACTION_START},
        )

    async def stop_charging(self) -> None:
        await self._request(
            "POST",
            f"/v2/charger/{self._charger_id}/remote-action",
            json={"action": _ACTION_STOP},
        )

    async def set_current_limit(self, amps: int) -> None:
        await self._request(
            "PUT",
            f"/v2/charger/{self._charger_id}",
            json={"maxChargingCurrent": amps},
        )
