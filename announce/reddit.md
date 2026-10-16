# r/homeassistant

**Titel:** School Holidays – custom integration for school-holiday sensors (openholidaysapi.org)

<!-- Bild/GIF hier einfügen: idealerweise die drei Entitäten (today / tomorrow /
     next_holiday mit days_until) oder ein kurzes GIF des Config-Flows.
     Auf Reddit als Bild-/Video-Post oder eingebettetes Bild hochladen. -->

*[Bild/GIF: today / tomorrow / next_holiday mit days_until]*

---

Small custom integration that exposes school holidays for a selectable country
and region as Home Assistant sensors. It provides two binary sensors (`today`,
`tomorrow`) and a `next_holiday` sensor (date, with a `days_until` attribute),
so you can automate around school holidays – e.g. skip the alarm, send a
notification, or show a countdown.

Country and region are picked in the UI, the update interval is configurable
(default 24 h), and data comes from the free openholidaysapi.org (no API key).
UI in en/de/es/fr, MIT licensed, needs HA 2025.2+.

Honest limits: coverage depends entirely on openholidaysapi.org, so check your
region first; and it only covers school holidays, not public holidays.

GitHub: https://github.com/Jo-Highness/school_holidays
