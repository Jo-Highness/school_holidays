# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.1] - 2026-08-21

### Added

- Continuous integration: **Validate** workflow (hassfest + HACS action) and
  **Test** workflow (ruff lint/format check + pytest).
- Test suite covering the config flow, entry setup/unload, and the coordinator's
  behaviour on an API error.
- Ruff configuration (`pyproject.toml`) with a curated lint rule set and isort settings.

### Changed

- `manifest.json` keys sorted to be hassfest-conform (`domain`/`name` first, then alphabetical).

### Fixed

- First setup with an unreachable API now raises `ConfigEntryNotReady` (so Home
  Assistant retries) instead of completing setup with empty data.

## [1.0.0] - 2026-07-29

### Added

- Initial release of the **School Holidays** integration.
- `binary_sensor` — *School holidays today* (`on` while today is within a holiday period).
- `binary_sensor` — *School holidays tomorrow*.
- `sensor` — *Next school holiday* with `holiday_name`, `start_date`, `end_date`
  and `days_until` attributes.
- UI config flow to pick country and state/region (two-step dropdown, no YAML).
- Holiday data from the free, key-less [openholidaysapi.org](https://openholidaysapi.org).
- Robust coordinator with a midnight rollover and keep-last-known-data behaviour
  when the API is briefly unreachable.
- Translations for English, German, Spanish and French.

[Unreleased]: https://github.com/Jo-Highness/school_holidays/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Jo-Highness/school_holidays/releases/tag/v1.0.0
