"""Config- and options-flow tests for School Holidays."""

from __future__ import annotations

from unittest.mock import patch

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.school_holidays import api
from custom_components.school_holidays.const import (
    CONF_COUNTRY,
    CONF_LANGUAGE,
    CONF_SUBDIVISION,
    CONF_SUBDIVISION_NAME,
    CONF_UPDATE_HOURS,
    DOMAIN,
    LANGUAGE_AUTO,
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
        result["flow_id"], {CONF_UPDATE_HOURS: 24, CONF_LANGUAGE: "EN"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options[CONF_UPDATE_HOURS] == 24


async def test_flow_subdivisions_unreachable_aborts(hass: HomeAssistant) -> None:
    """A failing subdivision lookup must abort, not silently pick the whole country."""
    with (
        patch(f"{API}.async_get_countries", return_value=COUNTRIES),
        patch(f"{API}.async_get_subdivisions", side_effect=api.OpenHolidaysError("boom")),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_COUNTRY: "DE"}
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"
    assert not hass.config_entries.async_entries(DOMAIN)


async def test_flow_regional_language_tag(hass: HomeAssistant) -> None:
    """A regional HA language like 'de-CH' is reduced to the ISO 639-1 code."""
    hass.config.language = "de-CH"
    with (
        patch(f"{API}.async_get_countries", return_value=COUNTRIES) as countries,
        patch(f"{API}.async_get_subdivisions", return_value=[]),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_COUNTRY: "DE"}
        )

    assert countries.call_args.args[1] == "DE"
    assert result["type"] is FlowResultType.CREATE_ENTRY
    # New entries follow the HA language instead of freezing it at setup time.
    assert result["data"][CONF_LANGUAGE] == LANGUAGE_AUTO


async def test_options_flow_language(hass: HomeAssistant, config_entry) -> None:
    """The holiday-name language can be switched to 'auto' or an explicit code."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    # Existing entries keep their explicit language as the default.
    schema = result["data_schema"].schema
    lang_key = next(k for k in schema if k == CONF_LANGUAGE)
    assert lang_key.default() == "EN"
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_UPDATE_HOURS: 24, CONF_LANGUAGE: "auto"}
    )
    assert config_entry.options[CONF_LANGUAGE] == LANGUAGE_AUTO

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_UPDATE_HOURS: 12, CONF_LANGUAGE: "fr-be"}
    )
    assert config_entry.options == {CONF_UPDATE_HOURS: 12, CONF_LANGUAGE: "FR"}


async def _reconfigure(hass: HomeAssistant, entry, subdivision: str):
    with (
        patch(f"{API}.async_get_countries", return_value=COUNTRIES),
        patch(f"{API}.async_get_subdivisions", return_value=SUBDIVISIONS),
        patch(f"{API}.async_get_school_holidays", return_value=[]),
    ):
        result = await entry.start_reconfigure_flow(hass)
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_COUNTRY: "DE"}
        )
        assert result["step_id"] == "subdivision"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_SUBDIVISION: subdivision}
        )
        await hass.async_block_till_done()
    return result


async def test_reconfigure_changes_region(hass: HomeAssistant, config_entry) -> None:
    """Reconfigure switches the region in place, keeping entry id and language."""
    config_entry.add_to_hass(hass)
    entry_id = config_entry.entry_id
    result = await _reconfigure(hass, config_entry, "DE-BY")
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    entry = hass.config_entries.async_get_entry(entry_id)
    assert entry.unique_id == "DE:DE-BY"
    assert entry.title == "Bavaria"
    assert entry.data[CONF_SUBDIVISION] == "DE-BY"
    assert entry.data[CONF_SUBDIVISION_NAME] == "Bavaria"
    assert entry.data[CONF_LANGUAGE] == "EN"


async def test_reconfigure_same_region(hass: HomeAssistant, config_entry) -> None:
    """Picking the current region again is fine (no 'already configured')."""
    config_entry.add_to_hass(hass)
    result = await _reconfigure(hass, config_entry, "DE-HE")
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.unique_id == "DE:DE-HE"


async def test_reconfigure_to_existing_region_aborts(hass: HomeAssistant, config_entry) -> None:
    """Reconfiguring onto a region that has its own entry is refused."""
    config_entry.add_to_hass(hass)
    MockConfigEntry(domain=DOMAIN, unique_id="DE:DE-BY", data={CONF_COUNTRY: "DE"}).add_to_hass(
        hass
    )
    result = await _reconfigure(hass, config_entry, "DE-BY")
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert config_entry.unique_id == "DE:DE-HE"
