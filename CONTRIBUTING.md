# Contributing

Thanks for your interest in improving **School Holidays**! This document explains
how to set up a development environment and how to get changes merged.

## Repository layout

```
custom_components/school_holidays/   # the integration
  __init__.py                        # setup/unload of the config entry
  api.py                             # async client for openholidaysapi.org
  binary_sensor.py                   # "today" / "tomorrow" binary sensors
  sensor.py                          # "next school holiday" sensor
  config_flow.py                     # UI config flow (country → region)
  coordinator.py                     # DataUpdateCoordinator (midnight rollover, keep-last)
  entity.py                          # shared base entity
  logic.py                           # date/holiday evaluation helpers
  const.py                           # constants
  manifest.json / strings.json       # integration metadata + UI strings
  translations/                      # en, de, es, fr
tests/                               # pytest suite
hacs.json                            # HACS metadata
pyproject.toml / pytest.ini          # ruff + pytest configuration
```

## Development setup

Requires **Python 3.13**.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install ruff pytest pytest-homeassistant-custom-component
```

The integration itself has **no runtime dependencies** (`requirements` is empty in
`manifest.json`); only the tooling above is needed for development.

## Checks before you open a PR

Run all three locally and make sure they pass:

```bash
ruff check .        # lint
ruff format .       # format (or: ruff format --check .)
pytest              # tests
```

The CI runs the same checks (see `.github/workflows/test.yml`) plus hassfest and
HACS validation (`.github/workflows/validate.yml`).

## Branches & commits

- Branch off `main`, e.g. `feat/next-holiday-attribute` or `fix/coordinator-retry`.
- Use [Conventional Commits](https://www.conventionalcommits.org/) for commit
  messages, e.g.:
  - `feat: add option to select multiple regions`
  - `fix(coordinator): keep last data on timeout`
  - `docs: clarify installation steps`
  - `test:`, `ci:`, `chore:`, `refactor:` as appropriate.

## Pull request process

1. Keep the PR focused on a single change.
2. Update `CHANGELOG.md` under `## [Unreleased]`.
3. Update documentation (README / translations) if behaviour or UI strings change.
4. Ensure `ruff check`, `ruff format --check` and `pytest` are green.
5. Fill in the PR template checklist. A maintainer will review and merge.

By contributing you agree that your contributions are licensed under the
project's [MIT License](LICENSE).
