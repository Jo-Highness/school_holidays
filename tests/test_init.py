"""Setup / unload / coordinator / entity tests for School Holidays."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    device_registry as dr,
    entity_registry as er,
    issue_registry as ir,
)
from homeassistant.util import dt as dt_util
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.school_holidays import api
from custom_components.school_holidays.const import (
    CONF_LANGUAGE,
    DATA_PERIODS,
    DOMAIN,
    LANGUAGE_AUTO,
)
from custom_components.school_holidays.coordinator import stale_issue_id
from custom_components.school_holidays.diagnostics import (
    async_get_config_entry_diagnostics,
)

API = "custom_components.school_holidays.api.async_get_school_holidays"


def _period(start: date, end: date, name: str) -> dict:
    return {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "name": [{"language": "EN", "text": name}, {"language": "DE", "text": f"{name} (de)"}],
    }


def _raw_today_holiday() -> list[dict]:
    """A single period spanning yesterday..tomorrow -> today & tomorrow are holidays."""
    today = dt_util.now().date()
    return [_period(today - timedelta(days=1), today + timedelta(days=1), "Autumn break")]


async def _setup(hass: HomeAssistant, entry, raw) -> None:
    entry.add_to_hass(hass)
    with patch(API, return_value=raw):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


def _eid(hass: HomeAssistant, entry, platform: str, key: str) -> str:
    ent_reg = er.async_get(hass)
    eid = ent_reg.async_get_entity_id(platform, DOMAIN, f"{entry.entry_id}_{key}")
    assert eid, f"entity {platform}/{key} not registered"
    return eid


@pytest.fixture
def noon(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> datetime:
    """Freeze time at local noon of a fixed day (2026-10-14, a Wednesday)."""
    now = dt_util.as_utc(datetime(2026, 10, 14, 12, 0, tzinfo=dt_util.get_default_time_zone()))
    freezer.move_to(now)
    return now


async def test_setup_creates_entities(hass: HomeAssistant, config_entry) -> None:
    """Setup registers the entities with correct state and runtime_data."""
    await _setup(hass, config_entry, _raw_today_holiday())
    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.runtime_data.data[DATA_PERIODS] == 1

    today = _eid(hass, config_entry, "binary_sensor", "today")
    tomorrow = _eid(hass, config_entry, "binary_sensor", "tomorrow")
    nxt = _eid(hass, config_entry, "sensor", "next_holiday")
    last = _eid(hass, config_entry, "sensor", "last_successful_update")

    assert hass.states.get(today).state == "on"
    assert hass.states.get(tomorrow).state == "on"
    assert hass.states.get(today).attributes["holiday_name"] == "Autumn break"

    nxt_state = hass.states.get(nxt)
    expected_start = (dt_util.now().date() - timedelta(days=1)).isoformat()
    assert nxt_state.state == expected_start
    assert nxt_state.attributes["holiday_name"] == "Autumn break"
    assert nxt_state.attributes["days_until"] == 0
    assert hass.states.get(last).state not in ("unknown", "unavailable")
    assert er.async_get(hass).async_get(last).entity_category == "diagnostic"


async def test_entity_ids_and_device(hass: HomeAssistant, config_entry) -> None:
    """Entity IDs are unchanged from 1.0.x and the device is a service device."""
    await _setup(hass, config_entry, _raw_today_holiday())
    assert _eid(hass, config_entry, "binary_sensor", "today") == (
        "binary_sensor.hesse_school_holidays_today"
    )
    assert _eid(hass, config_entry, "binary_sensor", "tomorrow") == (
        "binary_sensor.hesse_school_holidays_tomorrow"
    )
    assert _eid(hass, config_entry, "sensor", "next_holiday") == (
        "sensor.hesse_next_school_holiday"
    )
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, config_entry.entry_id)})
    assert device.entry_type is dr.DeviceEntryType.SERVICE
    assert device.name == "Hesse"


async def test_tomorrow_attributes_use_tomorrows_period(
    hass: HomeAssistant, config_entry, noon
) -> None:
    """Regression: 'tomorrow' must expose the period covering tomorrow, not today."""
    today = dt_util.now().date()
    raw = [_period(today + timedelta(days=1), today + timedelta(days=10), "Autumn break")]
    await _setup(hass, config_entry, raw)

    t = hass.states.get(_eid(hass, config_entry, "binary_sensor", "today"))
    tm = hass.states.get(_eid(hass, config_entry, "binary_sensor", "tomorrow"))
    assert t.state == "off"
    assert t.attributes["holiday_name"] is None
    assert tm.state == "on"
    assert tm.attributes["holiday_name"] == "Autumn break"
    assert tm.attributes["start_date"] == (today + timedelta(days=1)).isoformat()
    assert tm.attributes["end_date"] == (today + timedelta(days=10)).isoformat()

    nxt = hass.states.get(_eid(hass, config_entry, "sensor", "next_holiday"))
    assert nxt.state == (today + timedelta(days=1)).isoformat()
    assert nxt.attributes["days_until"] == 1


async def test_last_holiday_day_tomorrow_is_off(hass: HomeAssistant, config_entry, noon) -> None:
    """On the last holiday day, today has the period and tomorrow has none."""
    today = dt_util.now().date()
    await _setup(hass, config_entry, [_period(today - timedelta(days=3), today, "Break")])
    t = hass.states.get(_eid(hass, config_entry, "binary_sensor", "today"))
    tm = hass.states.get(_eid(hass, config_entry, "binary_sensor", "tomorrow"))
    assert (t.state, t.attributes["holiday_name"]) == ("on", "Break")
    assert (tm.state, tm.attributes["holiday_name"]) == ("off", None)


async def test_no_upcoming_holiday(hass: HomeAssistant, config_entry, noon) -> None:
    """Without any period, the date sensor is unknown and binaries are off."""
    today = dt_util.now().date()
    await _setup(
        hass, config_entry, [_period(today - timedelta(days=30), today - timedelta(days=20), "Old")]
    )
    assert hass.states.get(_eid(hass, config_entry, "sensor", "next_holiday")).state == "unknown"
    assert hass.states.get(_eid(hass, config_entry, "binary_sensor", "today")).state == "off"


async def test_midnight_rollover_without_network(
    hass: HomeAssistant, config_entry, noon, freezer: FrozenDateTimeFactory
) -> None:
    """At local midnight today/tomorrow are recomputed from cache, no API call."""
    today = dt_util.now().date()
    raw = [_period(today + timedelta(days=1), today + timedelta(days=5), "Autumn break")]
    await _setup(hass, config_entry, raw)
    today_eid = _eid(hass, config_entry, "binary_sensor", "today")
    assert hass.states.get(today_eid).state == "off"

    midnight = dt_util.start_of_local_day(today + timedelta(days=1)) + timedelta(seconds=5)
    with patch(API, side_effect=AssertionError("no network at midnight")) as mock_api:
        freezer.move_to(midnight)
        async_fire_time_changed(hass, midnight)
        await hass.async_block_till_done()
    assert not mock_api.called
    state = hass.states.get(today_eid)
    assert state.state == "on"
    assert state.attributes["holiday_name"] == "Autumn break"
    nxt = hass.states.get(_eid(hass, config_entry, "sensor", "next_holiday"))
    assert nxt.attributes["days_until"] == 0


async def test_unload_stops_midnight_timer(
    hass: HomeAssistant, config_entry, noon, freezer: FrozenDateTimeFactory
) -> None:
    """After unload the midnight timer is gone (registered via async_on_unload)."""
    await _setup(hass, config_entry, _raw_today_holiday())
    coordinator = config_entry.runtime_data
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    assert config_entry.state is ConfigEntryState.NOT_LOADED

    midnight = dt_util.start_of_local_day(dt_util.now().date() + timedelta(days=1)) + timedelta(
        seconds=5
    )
    with patch.object(coordinator, "_derive") as derive:
        freezer.move_to(midnight)
        async_fire_time_changed(hass, midnight)
        await hass.async_block_till_done()
    assert not derive.called


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
    coordinator = config_entry.runtime_data
    first_success = coordinator.last_successful_update

    with patch(API, side_effect=api.OpenHolidaysError("hiccup")):
        await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert coordinator.data[DATA_PERIODS] == 1
    assert coordinator.last_successful_update == first_success
    issue = ir.async_get(hass).async_get_issue(DOMAIN, stale_issue_id(config_entry.entry_id))
    assert issue is None  # a short outage does not raise a repair issue


async def test_stale_data_repair_issue(
    hass: HomeAssistant, config_entry, noon, freezer: FrozenDateTimeFactory
) -> None:
    """A long outage raises a repair issue; data is kept; success clears it."""
    today = dt_util.now().date()
    raw = [_period(today + timedelta(days=9), today + timedelta(days=20), "Break")]
    await _setup(hass, config_entry, raw)
    coordinator = config_entry.runtime_data
    issue_reg = ir.async_get(hass)
    issue_id = stale_issue_id(config_entry.entry_id)

    freezer.tick(timedelta(days=8))
    with patch(API, side_effect=api.OpenHolidaysError("down")):
        await coordinator.async_refresh()
    issue = issue_reg.async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.translation_key == "stale_data"
    assert issue.translation_placeholders["region"] == "Hesse"
    assert issue.translation_placeholders["days"] == "8"
    # Cached dates still cover today -> sensors keep working (day 9 = tomorrow).
    assert coordinator.data[DATA_PERIODS] == 1
    assert coordinator.data["tomorrow"] is True

    with patch(API, return_value=raw):
        await coordinator.async_refresh()
    assert issue_reg.async_get_issue(DOMAIN, issue_id) is None


async def test_remove_entry_deletes_issue(
    hass: HomeAssistant, config_entry, noon, freezer: FrozenDateTimeFactory
) -> None:
    """Deleting the entry also removes its repair issue."""
    await _setup(hass, config_entry, _raw_today_holiday())
    freezer.tick(timedelta(days=8))
    with patch(API, side_effect=api.OpenHolidaysError("down")):
        await config_entry.runtime_data.async_refresh()
    issue_id = stale_issue_id(config_entry.entry_id)
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is not None
    await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()
    assert ir.async_get(hass).async_get_issue(DOMAIN, issue_id) is None


async def test_language_explicit_is_kept(hass: HomeAssistant, config_entry) -> None:
    """Entries from <= 1.0.2 keep their explicit language regardless of HA language."""
    hass.config.language = "de"
    await _setup(hass, config_entry, _raw_today_holiday())
    assert config_entry.runtime_data.language == "EN"
    state = hass.states.get(_eid(hass, config_entry, "binary_sensor", "today"))
    assert state.attributes["holiday_name"] == "Autumn break"


async def test_language_follows_home_assistant(hass: HomeAssistant, config_entry) -> None:
    """language=auto follows the HA language and refetches when it changes."""
    hass.config.language = "de-CH"
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=config_entry.title,
        unique_id=config_entry.unique_id,
        data={**config_entry.data, CONF_LANGUAGE: LANGUAGE_AUTO},
    )
    entry.add_to_hass(hass)
    with patch(API, return_value=_raw_today_holiday()) as mock_api:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert mock_api.call_args.args[5] == "DE"
        state = hass.states.get(_eid(hass, entry, "binary_sensor", "today"))
        assert state.attributes["holiday_name"] == "Autumn break (de)"

        await hass.config.async_update(language="en")
        await hass.async_block_till_done()
        assert mock_api.call_count == 2
        assert mock_api.call_args.args[5] == "EN"
    state = hass.states.get(_eid(hass, entry, "binary_sensor", "today"))
    assert state.attributes["holiday_name"] == "Autumn break"


async def test_options_change_reloads_with_new_interval(hass: HomeAssistant, config_entry) -> None:
    """Default interval is 24 h; changing the option reloads with the new value."""
    await _setup(hass, config_entry, _raw_today_holiday())
    assert config_entry.runtime_data.update_interval == timedelta(hours=24)
    with patch(API, return_value=_raw_today_holiday()):
        hass.config_entries.async_update_entry(
            config_entry, options={"update_hours": 6, CONF_LANGUAGE: "EN"}
        )
        await hass.async_block_till_done()
    assert config_entry.runtime_data.update_interval == timedelta(hours=6)


async def test_diagnostics(hass: HomeAssistant, config_entry) -> None:
    """Diagnostics contain the entry, language and derived data."""
    await _setup(hass, config_entry, _raw_today_holiday())
    diag = await async_get_config_entry_diagnostics(hass, config_entry)
    assert diag["entry"]["data"]["subdivision"] == "DE-HE"
    assert diag["language_effective"] == "EN"
    assert diag["update_interval_hours"] == 24
    assert diag["stale_issue_active"] is False
    assert diag["data"]["periods"] == 1
    assert isinstance(diag["data"]["last_successful_update"], str)
