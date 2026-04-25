import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from integrations.solar.hoymiles import HoymilesClient


def _make_response(dtu_power: int, dtu_daily_energy: int, pv_energy_totals: list[int]):
    pv_data = []
    for energy_total in pv_energy_totals:
        pv = MagicMock()
        pv.energy_total = energy_total
        pv_data.append(pv)

    response = MagicMock()
    response.dtu_power = dtu_power
    response.dtu_daily_energy = dtu_daily_energy
    response.pv_data = pv_data
    return response


@pytest.fixture
def client():
    return HoymilesClient(ip="192.168.1.100")


async def test_get_production_single_panel(client):
    response = _make_response(dtu_power=12000, dtu_daily_energy=3500, pv_energy_totals=[1500000])

    with patch.object(client._dtu, "async_get_real_data_new", new=AsyncMock(return_value=response)):
        data = await client.get_production()

    assert data["status"] == "online"
    assert data["dc_power"] == pytest.approx(1200.0)        # 12000 / 10
    assert data["today_production"] == pytest.approx(3.5)   # 3500 / 1000
    assert data["total_production"] == pytest.approx(1500.0) # 1500000 / 1000


async def test_get_production_multiple_panels(client):
    response = _make_response(dtu_power=8000, dtu_daily_energy=2000, pv_energy_totals=[600000, 400000])

    with patch.object(client._dtu, "async_get_real_data_new", new=AsyncMock(return_value=response)):
        data = await client.get_production()

    assert data["dc_power"] == pytest.approx(800.0)         # 8000 / 10
    assert data["today_production"] == pytest.approx(2.0)
    assert data["total_production"] == pytest.approx(1000.0) # (600000 + 400000) / 1000


async def test_get_production_none_response_returns_offline(client):
    with patch.object(client._dtu, "async_get_real_data_new", new=AsyncMock(return_value=None)):
        data = await client.get_production()

    assert data["status"] == "offline"
    assert data["dc_power"] == 0.0


async def test_get_production_exception_returns_offline(client):
    with patch.object(client._dtu, "async_get_real_data_new", new=AsyncMock(side_effect=ConnectionError("timeout"))):
        data = await client.get_production()

    assert data["status"] == "offline"
    assert data["dc_power"] == 0.0
