"""Tests for the thin openholidaysapi.org client."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest

from custom_components.school_holidays import api

URL = f"{api.BASE}/SchoolHolidays"


async def test_school_holidays_ok(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, json=[{"startDate": "2026-10-05", "endDate": "2026-10-17"}])
    data = await api.async_get_school_holidays(
        async_get_clientsession(hass), "DE", "DE-HE", "2026-10-01", "2026-12-31"
    )
    assert data == [{"startDate": "2026-10-05", "endDate": "2026-10-17"}]
    assert aioclient_mock.mock_calls[0][1].query["subdivisionCode"] == "DE-HE"


async def test_http_error_raises(hass: HomeAssistant, aioclient_mock) -> None:
    aioclient_mock.get(URL, status=503)
    with pytest.raises(api.OpenHolidaysError):
        await api.async_get_school_holidays(
            async_get_clientsession(hass), "DE", None, "2026-10-01", "2026-12-31"
        )


async def test_unexpected_payload_raises(hass: HomeAssistant, aioclient_mock) -> None:
    """A non-list JSON body (e.g. an error object) is treated as an API failure."""
    aioclient_mock.get(URL, json={"title": "Bad Request"})
    with pytest.raises(api.OpenHolidaysError):
        await api.async_get_school_holidays(
            async_get_clientsession(hass), "DE", None, "2026-10-01", "2026-12-31"
        )
