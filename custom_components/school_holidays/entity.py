"""Base entity for School Holidays."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_COUNTRY_NAME, CONF_SUBDIVISION_NAME, DOMAIN
from .coordinator import SchoolHolidaysCoordinator


class SchoolHolidaysEntity(CoordinatorEntity[SchoolHolidaysCoordinator]):
    """Base class wiring entities to the coordinator + a per-region device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SchoolHolidaysCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{key}"
        opts = {**coordinator.entry.data, **coordinator.entry.options}
        region = opts.get(CONF_SUBDIVISION_NAME) or opts.get(CONF_COUNTRY_NAME) or "School holidays"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name=region,
            manufacturer="openholidaysapi.org",
            model="School holidays",
        )
