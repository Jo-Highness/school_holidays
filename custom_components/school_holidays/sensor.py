"""Sensors: the next (or current) school holiday + last successful update."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DATA_LAST_SUCCESS, DATA_NEXT
from .coordinator import SchoolHolidaysConfigEntry, SchoolHolidaysCoordinator
from .entity import SchoolHolidaysEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SchoolHolidaysConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    coordinator = entry.runtime_data
    async_add_entities([NextHolidaySensor(coordinator), LastUpdateSensor(coordinator)])


class NextHolidaySensor(SchoolHolidaysEntity, SensorEntity):
    """State = start date of the current/next holiday; details in attributes."""

    _attr_translation_key = "next_holiday"
    _attr_device_class = SensorDeviceClass.DATE

    def __init__(self, coordinator: SchoolHolidaysCoordinator) -> None:
        super().__init__(coordinator, "next_holiday")

    @property
    def native_value(self) -> date | None:
        nxt = (self.coordinator.data or {}).get(DATA_NEXT)
        if not nxt or not nxt.get("start"):
            return None
        try:
            return datetime.strptime(nxt["start"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        nxt = (self.coordinator.data or {}).get(DATA_NEXT) or {}
        return {
            "holiday_name": nxt.get("name"),
            "start_date": nxt.get("start"),
            "end_date": nxt.get("end"),
            "days_until": nxt.get("days_until"),
        }


class LastUpdateSensor(SchoolHolidaysEntity, SensorEntity):
    """Diagnostic: when holiday data was last fetched successfully."""

    _attr_translation_key = "last_successful_update"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: SchoolHolidaysCoordinator) -> None:
        super().__init__(coordinator, "last_successful_update")

    @property
    def native_value(self) -> datetime | None:
        return (self.coordinator.data or {}).get(DATA_LAST_SUCCESS)
