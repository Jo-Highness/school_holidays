"""Sensor: the next (or current) school holiday."""
from __future__ import annotations

from datetime import date, datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_NEXT, DOMAIN
from .coordinator import SchoolHolidaysCoordinator
from .entity import SchoolHolidaysEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SchoolHolidaysCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([NextHolidaySensor(coordinator)])


class NextHolidaySensor(SchoolHolidaysEntity, SensorEntity):
    """State = start date of the current/next holiday; details in attributes."""

    _attr_translation_key = "next_holiday"
    _attr_icon = "mdi:calendar-star"
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
    def extra_state_attributes(self) -> dict:
        nxt = (self.coordinator.data or {}).get(DATA_NEXT) or {}
        return {
            "holiday_name": nxt.get("name"),
            "start_date": nxt.get("start"),
            "end_date": nxt.get("end"),
            "days_until": nxt.get("days_until"),
        }
