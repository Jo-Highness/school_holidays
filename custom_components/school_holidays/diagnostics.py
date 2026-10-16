"""Diagnostics for School Holidays."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .coordinator import SchoolHolidaysConfigEntry, stale_issue_id


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SchoolHolidaysConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry.

    Only a country/region code and public holiday dates are involved, so nothing
    needs redacting.
    """
    coordinator = entry.runtime_data
    last = coordinator.last_successful_update
    return {
        "entry": {
            "title": entry.title,
            "version": entry.version,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
        "language_setting": coordinator.language_setting,
        "language_effective": coordinator.language,
        "update_interval_hours": (
            coordinator.update_interval.total_seconds() / 3600
            if coordinator.update_interval
            else None
        ),
        "last_update_success": coordinator.last_update_success,
        "last_successful_update": last.isoformat() if last else None,
        "stale_issue_active": ir.async_get(hass).async_get_issue(
            DOMAIN, stale_issue_id(entry.entry_id)
        )
        is not None,
        "data": {
            k: (v.isoformat() if hasattr(v, "isoformat") else v)
            for k, v in (coordinator.data or {}).items()
        },
    }
