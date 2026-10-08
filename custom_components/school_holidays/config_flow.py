"""Config & options flow for School Holidays (pick country + subdivision)."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from . import api
from .const import (
    CONF_COUNTRY,
    CONF_COUNTRY_NAME,
    CONF_LANGUAGE,
    CONF_SUBDIVISION,
    CONF_SUBDIVISION_NAME,
    CONF_UPDATE_HOURS,
    DEFAULT_LANGUAGE,
    DEFAULT_UPDATE_HOURS,
    DOMAIN,
)


def _select(options: list[dict[str, str]]) -> selector.SelectSelector:
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=o["value"], label=o["label"]) for o in options
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


class SchoolHolidaysConfigFlow(ConfigFlow, domain=DOMAIN):
    """Two steps: country, then subdivision."""

    VERSION = 1

    def __init__(self) -> None:
        self._country: str | None = None
        self._country_name: str = ""
        self._countries: list[dict] = []
        self._subdivisions: list[dict] = []

    def _language(self) -> str:
        # HA may use regional tags like "en-GB" / "pt-BR"; the API wants ISO 639-1.
        lang = (self.hass.config.language or DEFAULT_LANGUAGE).split("-")[0].upper()
        return lang if len(lang) == 2 else DEFAULT_LANGUAGE

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if not self._countries:
            try:
                session = async_get_clientsession(self.hass)
                self._countries = await api.async_get_countries(session, self._language())
            except api.OpenHolidaysError:
                return self.async_abort(reason="cannot_connect")
        if user_input is not None:
            self._country = user_input[CONF_COUNTRY]
            self._country_name = next(
                (c["name"] for c in self._countries if c["code"] == self._country), self._country
            )
            return await self.async_step_subdivision()
        opts = [{"value": c["code"], "label": c["name"]} for c in self._countries]
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_COUNTRY): _select(opts)}),
            errors=errors,
        )

    async def async_step_subdivision(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        if not self._subdivisions:
            try:
                session = async_get_clientsession(self.hass)
                self._subdivisions = await api.async_get_subdivisions(
                    session, self._country, self._language()
                )
            except api.OpenHolidaysError:
                # Do NOT fall through to "whole country": for countries with
                # regional holidays (e.g. DE) that would silently mix every
                # region's holidays into one entry.
                return self.async_abort(reason="cannot_connect")
        # Countries without subdivisions -> configure the whole country directly.
        if not self._subdivisions:
            return await self._create(None, "")
        if user_input is not None:
            code = user_input.get(CONF_SUBDIVISION) or None
            name = next((s["name"] for s in self._subdivisions if s["code"] == code), "")
            return await self._create(code, name)
        opts = [{"value": s["code"], "label": s["name"]} for s in self._subdivisions]
        return self.async_show_form(
            step_id="subdivision",
            data_schema=vol.Schema({vol.Required(CONF_SUBDIVISION): _select(opts)}),
        )

    async def _create(self, subdivision: str | None, subdivision_name: str) -> ConfigFlowResult:
        unique = f"{self._country}:{subdivision or '-'}"
        await self.async_set_unique_id(unique)
        self._abort_if_unique_id_configured()
        title = subdivision_name or self._country_name
        return self.async_create_entry(
            title=title,
            data={
                CONF_COUNTRY: self._country,
                CONF_COUNTRY_NAME: self._country_name,
                CONF_SUBDIVISION: subdivision,
                CONF_SUBDIVISION_NAME: subdivision_name,
                CONF_LANGUAGE: self._language(),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> SchoolHolidaysOptionsFlow:
        return SchoolHolidaysOptionsFlow(entry)


class SchoolHolidaysOptionsFlow(OptionsFlow):
    """Adjust the refresh interval."""

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        current = {**self._entry.data, **self._entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_HOURS,
                        default=current.get(CONF_UPDATE_HOURS, DEFAULT_UPDATE_HOURS),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=168,
                            step=1,
                            unit_of_measurement="h",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
        )
