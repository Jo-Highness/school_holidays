"""DataUpdateCoordinator for School Holidays."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from . import api, logic
from .const import (
    CONF_COUNTRY,
    CONF_LANGUAGE,
    CONF_SUBDIVISION,
    CONF_UPDATE_HOURS,
    DATA_CURRENT,
    DATA_NEXT,
    DATA_PERIODS,
    DATA_TODAY,
    DATA_TOMORROW,
    DEFAULT_LANGUAGE,
    DEFAULT_UPDATE_HOURS,
    DOMAIN,
    LOOKAHEAD_DAYS,
)

_LOGGER = logging.getLogger(__name__)


def _period_dict(p: logic.Period | None) -> dict | None:
    if p is None:
        return None
    return {"name": p.name, "start": p.start.isoformat(), "end": p.end.isoformat()}


class SchoolHolidaysCoordinator(DataUpdateCoordinator[dict]):
    """Fetches holiday periods and derives today/tomorrow/next, robustly."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        opts = {**entry.data, **entry.options}
        self.country = opts[CONF_COUNTRY]
        self.subdivision = opts.get(CONF_SUBDIVISION) or None
        self.language = opts.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        hours = int(opts.get(CONF_UPDATE_HOURS, DEFAULT_UPDATE_HOURS))
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=max(1, hours)),
        )
        self._periods: list[logic.Period] = []
        self._unsub_midnight = None

    async def async_setup(self) -> None:
        await self.async_config_entry_first_refresh()
        # Recompute today/tomorrow at local midnight WITHOUT a network call, so
        # the sensors flip exactly at the day boundary even if the API is down.
        self._unsub_midnight = async_track_time_change(
            self.hass, self._handle_midnight, hour=0, minute=0, second=5
        )

    async def async_shutdown(self) -> None:  # type: ignore[override]
        if self._unsub_midnight:
            self._unsub_midnight()
            self._unsub_midnight = None
        await super().async_shutdown()

    @callback
    def _handle_midnight(self, _now) -> None:
        self.async_set_updated_data(self._derive())

    def _derive(self) -> dict:
        today = dt_util.now().date()
        tomorrow = today + timedelta(days=1)
        current = logic.period_on(today, self._periods)
        nxt = logic.current_or_next(today, self._periods)
        nxt_dict = _period_dict(nxt)
        if nxt_dict is not None:
            nxt_dict["days_until"] = logic.days_until(today, nxt)
        return {
            DATA_PERIODS: len(self._periods),
            DATA_TODAY: logic.is_holiday(today, self._periods),
            DATA_TOMORROW: logic.is_holiday(tomorrow, self._periods),
            DATA_CURRENT: _period_dict(current),
            DATA_NEXT: nxt_dict,
        }

    async def _async_update_data(self) -> dict:
        today = dt_util.now().date()
        valid_from = today.isoformat()
        valid_to = (today + timedelta(days=LOOKAHEAD_DAYS)).isoformat()
        session = async_get_clientsession(self.hass)
        try:
            raw = await api.async_get_school_holidays(
                session, self.country, self.subdivision, valid_from, valid_to, self.language
            )
            self._periods = logic.parse_periods(raw, self.language)
        except api.OpenHolidaysError as err:
            # Robustness: once we have data, keep the last known periods instead of
            # going unavailable, so automations keep working through API hiccups.
            if self._periods:
                _LOGGER.warning("School holidays API failed (%s); keeping last data", err)
            else:
                # No cached data yet (e.g. the very first refresh): surface the
                # failure so Home Assistant retries the setup instead of silently
                # creating empty sensors. On the first refresh this becomes
                # ConfigEntryNotReady automatically.
                raise UpdateFailed(f"School holidays API unavailable: {err}") from err
        return self._derive()
