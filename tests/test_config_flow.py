"""Config- and options-flow tests for School Holidays."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.school_holidays import api
from custom_components.school_holidays.const import (
    CONF_COUNTRY,
    CONF_SUBDIVISION,
    CONF_UPDATE_HOURS,
    DOMAIN,
)

from .conftest import COUNTRIES, SUBDIVISIONS

API = "custom_components.school_holidays.api"


async def test_flow_happy_path(hass: HomeAssistant) -> None:
    """Country -> subdivision -> entry created."""
    with (
        patch(f"{API}.async_get_countries", return_value=COUNTRIES),
        patch(f"{API}.async_get_subdivisions", return_value=SUBDIVISIONS),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_COUNTRY: "DE"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "subdivision"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_SUBDIVISION: "DE-HE"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hesse"
    assert result["data"][CONF_COUNTRY] == "DE"
    assert result["data"][CONF_SUBDIVISION] == "DE-HE"


async def test_flow_cannot_connect(hass: HomeAssistant) -> None:
    """The country list is unreachable -> abort cannot_connect."""
    with patch(f"{API}.async_get_countries", side_effect=api.OpenHolidaysError("boom")):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


async def test_flow_country_without_subdivisions(hass: HomeAssistant) -> None:
    """A country without subdivisions is configured directly."""
    with (
        patch(f"{API}.async_get_countries", return_value=COUNTRIES),
        patch(f"{API}.async_get_subdivisions", return_value=[]),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_COUNTRY: "DE"}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Germany"
    assert result["data"][CONF_SUBDIVISION] is None


async def test_flow_duplicate_aborts(hass: HomeAssistant) -> None:
    """The same country/subdivision cannot be added twice."""
    with (
        patch(f"{API}.async_get_countries", return_value=COUNTRIES),
        patch(f"{API}.async_get_subdivisions", return_value=SUBDIVISIONS),
    ):
        for _ in range(2):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_COUNTRY: "DE"}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"], {CONF_SUBDIVISION: "DE-HE"}
            )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_update_hours(hass: HomeAssistant, config_entry) -> None:
    """The refresh interval can be changed via the options flow."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_UPDATE_HOURS: 24}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options[CONF_UPDATE_HOURS] == 24
