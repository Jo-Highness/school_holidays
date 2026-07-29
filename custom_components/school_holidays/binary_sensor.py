"""Binary sensors: school holidays today / tomorrow."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_CURRENT, DATA_TODAY, DATA_TOMORROW, DOMAIN
from .coordinator import SchoolHolidaysCoordinator
from .entity import SchoolHolidaysEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: SchoolHolidaysCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        HolidayTodayBinarySensor(coordinator),
        HolidayTomorrowBinarySensor(coordinator),
    ])


class _HolidayBinary(SchoolHolidaysEntity, BinarySensorEntity):
    _attr_icon = "mdi:school-outline"
    _data_key = DATA_TODAY

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        val = data.get(self._data_key)
        return bool(val) if val is not None else None

    @property
    def extra_state_attributes(self) -> dict:
        cur = (self.coordinator.data or {}).get(DATA_CURRENT) or {}
        return {
            "holiday_name": cur.get("name"),
            "start_date": cur.get("start"),
            "end_date": cur.get("end"),
        }


class HolidayTodayBinarySensor(_HolidayBinary):
    _attr_translation_key = "today"
    _data_key = DATA_TODAY

    def __init__(self, coordinator: SchoolHolidaysCoordinator) -> None:
        super().__init__(coordinator, "today")


class HolidayTomorrowBinarySensor(_HolidayBinary):
    _attr_translation_key = "tomorrow"
    _attr_icon = "mdi:calendar-arrow-right"
    _data_key = DATA_TOMORROW

    def __init__(self, coordinator: SchoolHolidaysCoordinator) -> None:
        super().__init__(coordinator, "tomorrow")
