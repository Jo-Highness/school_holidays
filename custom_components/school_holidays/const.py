"""Constants for the School Holidays integration."""
from __future__ import annotations

from datetime import timedelta

DOMAIN = "school_holidays"

CONF_COUNTRY = "country"
CONF_SUBDIVISION = "subdivision"
CONF_COUNTRY_NAME = "country_name"
CONF_SUBDIVISION_NAME = "subdivision_name"
CONF_LANGUAGE = "language"
CONF_UPDATE_HOURS = "update_hours"

DEFAULT_LANGUAGE = "EN"
DEFAULT_UPDATE_HOURS = 12
# How far ahead to fetch holiday periods (covers a full school year + buffer).
LOOKAHEAD_DAYS = 400

# Refresh cadence is derived from CONF_UPDATE_HOURS; this is the fallback.
DEFAULT_SCAN_INTERVAL = timedelta(hours=DEFAULT_UPDATE_HOURS)

# Coordinator data keys.
DATA_PERIODS = "periods"
DATA_TODAY = "today"
DATA_TOMORROW = "tomorrow"
DATA_CURRENT = "current"  # dict name/start/end or None
DATA_NEXT = "next"        # dict name/start/end/days_until or None
