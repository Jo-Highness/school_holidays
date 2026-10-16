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

# Language value meaning "follow the Home Assistant language" (default for new
# entries since 1.1.0). Entries created before 1.1.0 keep their explicit code.
LANGUAGE_AUTO = "auto"
DEFAULT_LANGUAGE = "EN"
# Offered in the options flow; any other ISO 639-1 code can be typed in.
LANGUAGE_CHOICES = ["EN", "DE", "FR", "ES", "IT", "NL", "PL", "PT", "CS", "SK", "HU", "RO"]

DEFAULT_UPDATE_HOURS = 24
MIN_UPDATE_HOURS = 1
MAX_UPDATE_HOURS = 168
# How far ahead to fetch holiday periods (covers a full school year + buffer).
LOOKAHEAD_DAYS = 400
# After this long without a successful refresh a repair issue is raised. The
# cached periods are still used, because they cover the next ~13 months.
STALE_AFTER = timedelta(days=7)
ISSUE_STALE_DATA = "stale_data"

# Coordinator data keys.
DATA_PERIODS = "periods"
DATA_TODAY = "today"
DATA_TOMORROW = "tomorrow"
DATA_CURRENT = "current"  # period covering today: dict name/start/end or None
DATA_TOMORROW_PERIOD = "tomorrow_period"  # period covering tomorrow or None
DATA_NEXT = "next"  # dict name/start/end/days_until or None
DATA_LAST_SUCCESS = "last_successful_update"  # aware datetime or None
