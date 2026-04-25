import pytest
from unittest.mock import AsyncMock, MagicMock
from core.energy_manager import EnergyManager, EmsMode


@pytest.fixture
def settings():
    s = MagicMock()
    s.ems_default_mode = "manual"
    s.ems_threshold_on_w = 1400
    s.ems_threshold_off_w = 500
    s.ems_histeresi_minuts = 0  # disabled in tests
    s.ems_voltage = 230
    s.ems_phases = 3
    return s


@pytest.fixture
def em(settings):
    solar = AsyncMock()
    wallbox = AsyncMock()
    mqtt = AsyncMock()
    influx = AsyncMock()
    solar.get_production.return_value = {
        "dc_power": 0.0, "today_production": 0.0, "total_production": 0.0, "status": "online"
    }
    wallbox.get_status.return_value = {
        "status": "ready", "charging_power": 0.0, "max_charging_current": 6,
        "session_energy": 0.0, "locked": False,
    }
    return EnergyManager(settings, solar, wallbox, mqtt, influx)


async def test_manual_mode_never_controls_wallbox(em):
    em.set_mode(EmsMode.MANUAL)
    em._solar.get_production.return_value["dc_power"] = 3000.0

    await em.tick()

    em._wallbox.start_charging.assert_not_called()
    em._wallbox.stop_charging.assert_not_called()


async def test_auto_starts_charging_above_threshold(em):
    em.set_mode(EmsMode.AUTO)
    em._solar.get_production.return_value["dc_power"] = 2000.0

    await em.tick()

    em._wallbox.start_charging.assert_called_once()
    assert em.last_action == "start_charging"


async def test_auto_does_not_start_below_threshold(em):
    em.set_mode(EmsMode.AUTO)
    em._solar.get_production.return_value["dc_power"] = 1000.0

    await em.tick()

    em._wallbox.start_charging.assert_not_called()


async def test_auto_stops_charging_below_off_threshold(em):
    em.set_mode(EmsMode.AUTO)
    em._charging_active = True
    em._solar.get_production.return_value["dc_power"] = 200.0

    await em.tick()

    em._wallbox.stop_charging.assert_called_once()
    assert em.last_action == "stop_charging"


async def test_eco_sets_minimum_current_when_low_surplus(em):
    em.set_mode(EmsMode.ECO)
    # 1000 W / 230 V / 3 phases ≈ 1.4 A → clamped to 6 A
    em._solar.get_production.return_value["dc_power"] = 1000.0

    await em.tick()

    em._wallbox.set_current_limit.assert_called_with(6)


async def test_eco_sets_correct_current_from_surplus(em):
    em.set_mode(EmsMode.ECO)
    # 6900 W / 230 V / 3 phases = 10 A
    em._solar.get_production.return_value["dc_power"] = 6900.0

    await em.tick()

    em._wallbox.set_current_limit.assert_called_with(10)


async def test_eco_caps_current_at_32a(em):
    em.set_mode(EmsMode.ECO)
    # 30000 W / 230 V / 3 phases ≈ 43 A → clamped to 32 A
    em._solar.get_production.return_value["dc_power"] = 30000.0

    await em.tick()

    em._wallbox.set_current_limit.assert_called_with(32)
