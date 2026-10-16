"""Base entity for School Holidays."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_COUNTRY_NAME, CONF_SUBDIVISION_NAME, DOMAIN
from .coordinator import SchoolHolidaysCoordinator


class SchoolHolidaysEntity(CoordinatorEntity[SchoolHolidaysCoordinator]):
    """Base class wiring entities to the coordinator + a per-region service device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: SchoolHolidaysCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        entry = coordinator.config_entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        opts = {**entry.data, **entry.options}
        region = opts.get(CONF_SUBDIVISION_NAME) or opts.get(CONF_COUNTRY_NAME)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="openholidaysapi.org",
            model="School holidays",
            # Without a region name, fall back to a translated device name.
            **({"name": region} if region else {"translation_key": "school_holidays"}),
        )
