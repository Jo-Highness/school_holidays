"""Setup / unload / coordinator tests for School Holidays."""

from __future__ import annotations

from datetime import timedelta
from unittest.mock import patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.school_holidays import api
from custom_components.school_holidays.const import DATA_PERIODS, DOMAIN

API = "custom_components.school_holidays.api.async_get_school_holidays"


def _raw_today_holiday() -> list[dict]:
    """A single period spanning yesterday..tomorrow -> today & tomorrow are holidays."""
    today = dt_util.now().date()
    return [
        {
            "startDate": (today - timedelta(days=1)).isoformat(),
            "endDate": (today + timedelta(days=1)).isoformat(),
            "name": [{"language": "EN", "text": "Autumn break"}],
        }
    ]


async def _setup(hass: HomeAssistant, entry, raw) -> None:
    entry.add_to_hass(hass)
    with patch(API, return_value=raw):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


def _eid(hass: HomeAssistant, entry, platform: str, key: str) -> str:
    ent_reg = er.async_get(hass)
    eid = ent_reg.async_get_entity_id(platform, DOMAIN, f"{entry.entry_id}_{key}")
    assert eid, f"entity {platform}/{key} not registered"
    return eid


async def test_setup_creates_entities(hass: HomeAssistant, config_entry) -> None:
    """Setup registers the two binary sensors + the next-holiday sensor with correct state."""
    await _setup(hass, config_entry, _raw_today_holiday())
    assert config_entry.state is ConfigEntryState.LOADED

    today = _eid(hass, config_entry, "binary_sensor", "today")
    tomorrow = _eid(hass, config_entry, "binary_sensor", "tomorrow")
    nxt = _eid(hass, config_entry, "sensor", "next_holiday")

    assert hass.states.get(today).state == "on"
    assert hass.states.get(tomorrow).state == "on"
    today_attrs = hass.states.get(today).attributes
    assert today_attrs["holiday_name"] == "Autumn break"

    nxt_state = hass.states.get(nxt)
    assert nxt_state.attributes["holiday_name"] == "Autumn break"
    assert nxt_state.attributes["days_until"] == 0


async def test_unload(hass: HomeAssistant, config_entry) -> None:
    """The entry unloads cleanly and drops its coordinator."""
    await _setup(hass, config_entry, _raw_today_holiday())
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED
    assert config_entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_first_refresh_api_error_is_not_ready(hass: HomeAssistant, config_entry) -> None:
    """API down on the very first refresh -> ConfigEntryNotReady (retry), not empty."""
    config_entry.add_to_hass(hass)
    with patch(API, side_effect=api.OpenHolidaysError("down")):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_api_hiccup_keeps_last_data(hass: HomeAssistant, config_entry) -> None:
    """After a successful load, a later API failure keeps the cached periods."""
    await _setup(hass, config_entry, _raw_today_holiday())
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    assert coordinator.data[DATA_PERIODS] == 1

    with patch(API, side_effect=api.OpenHolidaysError("hiccup")):
        await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert coordinator.data[DATA_PERIODS] == 1
