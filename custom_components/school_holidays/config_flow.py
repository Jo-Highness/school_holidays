"""Config, reconfigure & options flow for School Holidays."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from . import api, logic
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
    LANGUAGE_AUTO,
    LANGUAGE_CHOICES,
    MAX_UPDATE_HOURS,
    MIN_UPDATE_HOURS,
)
from .coordinator import SchoolHolidaysConfigEntry


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
    """Two steps: country, then subdivision. Also used for reconfigure."""

    VERSION = 1

    def __init__(self) -> None:
        self._country: str | None = None
        self._country_name: str = ""
        self._countries: list[dict] = []
        self._subdivisions: list[dict] = []

    def _language(self) -> str:
        """HA UI language as ISO 639-1 (used for the dropdown labels)."""
        return logic.iso_language(self.hass.config.language, DEFAULT_LANGUAGE)

    def _current(self, key: str) -> Any:
        """Current value of an existing entry while reconfiguring, else None."""
        if self.source != SOURCE_RECONFIGURE:
            return None
        return self._get_reconfigure_entry().data.get(key)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change country/region of an existing entry without deleting it."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if not self._countries:
            try:
                session = async_get_clientsession(self.hass)
                self._countries = await api.async_get_countries(session, self._language())
            except api.OpenHolidaysError:
                return self.async_abort(reason="cannot_connect")
        if user_input is not None:
            country = user_input[CONF_COUNTRY]
            if country != self._country:
                self._subdivisions = []
            self._country = country
            self._country_name = next(
                (c["name"] for c in self._countries if c["code"] == self._country), self._country
            )
            return await self.async_step_subdivision()
        opts = [{"value": c["code"], "label": c["name"]} for c in self._countries]
        schema = vol.Schema({vol.Required(CONF_COUNTRY): _select(opts)})
        if (current := self._current(CONF_COUNTRY)) is not None:
            schema = self.add_suggested_values_to_schema(schema, {CONF_COUNTRY: current})
        return self.async_show_form(step_id="user", data_schema=schema)

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
            return await self._finish(None, "")
        if user_input is not None:
            code = user_input.get(CONF_SUBDIVISION) or None
            name = next((s["name"] for s in self._subdivisions if s["code"] == code), "")
            return await self._finish(code, name)
        opts = [{"value": s["code"], "label": s["name"]} for s in self._subdivisions]
        schema = vol.Schema({vol.Required(CONF_SUBDIVISION): _select(opts)})
        current = self._current(CONF_SUBDIVISION)
        if current and any(s["code"] == current for s in self._subdivisions):
            schema = self.add_suggested_values_to_schema(schema, {CONF_SUBDIVISION: current})
        return self.async_show_form(step_id="subdivision", data_schema=schema)

    async def _finish(self, subdivision: str | None, subdivision_name: str) -> ConfigFlowResult:
        unique = f"{self._country}:{subdivision or '-'}"
        title = subdivision_name or self._country_name
        location = {
            CONF_COUNTRY: self._country,
            CONF_COUNTRY_NAME: self._country_name,
            CONF_SUBDIVISION: subdivision,
            CONF_SUBDIVISION_NAME: subdivision_name,
        }
        if self.source == SOURCE_RECONFIGURE:
            entry = self._get_reconfigure_entry()
            if unique != entry.unique_id and any(
                e.unique_id == unique
                for e in self._async_current_entries(include_ignore=False)
                if e.entry_id != entry.entry_id
            ):
                return self.async_abort(reason="already_configured")
            # Keep the stored language (explicit code or "auto") as it is.
            return self.async_update_reload_and_abort(
                entry, unique_id=unique, title=title, data_updates=location
            )
        await self.async_set_unique_id(unique)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=title,
            # New entries follow the Home Assistant language for holiday names.
            data={**location, CONF_LANGUAGE: LANGUAGE_AUTO},
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: SchoolHolidaysConfigEntry) -> SchoolHolidaysOptionsFlow:
        return SchoolHolidaysOptionsFlow()


class SchoolHolidaysOptionsFlow(OptionsFlow):
    """Refresh interval and holiday-name language."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            language = str(user_input.get(CONF_LANGUAGE) or LANGUAGE_AUTO).strip()
            language = (
                LANGUAGE_AUTO
                if language.lower() == LANGUAGE_AUTO
                else logic.iso_language(language, DEFAULT_LANGUAGE)
            )
            return self.async_create_entry(
                data={
                    CONF_UPDATE_HOURS: int(user_input[CONF_UPDATE_HOURS]),
                    CONF_LANGUAGE: language,
                }
            )
        current = {**self.config_entry.data, **self.config_entry.options}
        current_lang = str(current.get(CONF_LANGUAGE) or LANGUAGE_AUTO)
        if current_lang.lower() == LANGUAGE_AUTO:
            current_lang = LANGUAGE_AUTO
        choices = [LANGUAGE_AUTO, *LANGUAGE_CHOICES]
        if current_lang not in choices:
            choices.append(current_lang)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_HOURS,
                        default=int(current.get(CONF_UPDATE_HOURS, DEFAULT_UPDATE_HOURS)),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=MIN_UPDATE_HOURS,
                            max=MAX_UPDATE_HOURS,
                            step=1,
                            unit_of_measurement="h",
                            mode=selector.NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Required(CONF_LANGUAGE, default=current_lang): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=choices,
                            mode=selector.SelectSelectorMode.DROPDOWN,
                            custom_value=True,
                            translation_key="language",
                        )
                    ),
                }
            ),
        )
