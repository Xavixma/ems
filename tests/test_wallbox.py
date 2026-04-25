import pytest
import respx
import httpx
from integrations.wallbox.pulsar import WallboxClient

_BASE = "https://api.wall-box.com"
_CHARGER_ID = 12345
_TOKEN_RESP = {"data": {"attributes": {"token": "test-token"}}}


@pytest.fixture
async def client():
    c = WallboxClient(email="test@example.com", password="secret", charger_id=_CHARGER_ID)
    yield c
    await c.close()


@respx.mock
async def test_get_status_authenticates_and_returns_data(client):
    respx.get(f"{_BASE}/auth/token/user").mock(
        return_value=httpx.Response(200, json=_TOKEN_RESP)
    )
    respx.get(f"{_BASE}/v2/charger/{_CHARGER_ID}/status").mock(
        return_value=httpx.Response(200, json={
            "status_id": 193,
            "charging_power": 6900.0,
            "max_charging_current": 10,
            "added_energy": 2.5,
            "locked": False,
        })
    )

    status = await client.get_status()

    assert status["charging_power"] == 6900.0
    assert status["max_charging_current"] == 10
    assert status["locked"] is False


@respx.mock
async def test_set_current_limit(client):
    client._token = "pre-set-token"
    route = respx.put(f"{_BASE}/v2/charger/{_CHARGER_ID}").mock(
        return_value=httpx.Response(200, json={})
    )

    await client.set_current_limit(10)

    assert route.called
    assert route.calls[0].request.content == b'{"maxChargingCurrent": 10}'


@respx.mock
async def test_token_refresh_on_401(client):
    client._token = "expired-token"
    respx.get(f"{_BASE}/v2/charger/{_CHARGER_ID}/status").mock(side_effect=[
        httpx.Response(401),
        httpx.Response(200, json={
            "status_id": 0, "charging_power": 0,
            "max_charging_current": 6, "added_energy": 0, "locked": False,
        }),
    ])
    respx.get(f"{_BASE}/auth/token/user").mock(
        return_value=httpx.Response(200, json=_TOKEN_RESP)
    )

    status = await client.get_status()
    assert status["status"] == "0"
