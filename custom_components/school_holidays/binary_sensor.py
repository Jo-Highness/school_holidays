"""Binary sensors: school holidays today / tomorrow."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_CURRENT, DATA_TODAY, DATA_TOMORROW, DATA_TOMORROW_PERIOD
from .coordinator import SchoolHolidaysConfigEntry, SchoolHolidaysCoordinator
from .entity import SchoolHolidaysEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SchoolHolidaysConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the today / tomorrow binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            HolidayTodayBinarySensor(coordinator),
            HolidayTomorrowBinarySensor(coordinator),
        ]
    )


class _HolidayBinary(SchoolHolidaysEntity, BinarySensorEntity):
    """On while the given day is inside a holiday period.

    The attributes describe the period covering *that* day (today resp. tomorrow).
    """

    _data_key: str
    _period_key: str

    @property
    def is_on(self) -> bool | None:
        val = (self.coordinator.data or {}).get(self._data_key)
        return bool(val) if val is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        period = (self.coordinator.data or {}).get(self._period_key) or {}
        return {
            "holiday_name": period.get("name"),
            "start_date": period.get("start"),
            "end_date": period.get("end"),
        }


class HolidayTodayBinarySensor(_HolidayBinary):
    _attr_translation_key = "today"
    _data_key = DATA_TODAY
    _period_key = DATA_CURRENT

    def __init__(self, coordinator: SchoolHolidaysCoordinator) -> None:
        super().__init__(coordinator, "today")


class HolidayTomorrowBinarySensor(_HolidayBinary):
    _attr_translation_key = "tomorrow"
    _data_key = DATA_TOMORROW
    _period_key = DATA_TOMORROW_PERIOD

    def __init__(self, coordinator: SchoolHolidaysCoordinator) -> None:
        super().__init__(coordinator, "tomorrow")
