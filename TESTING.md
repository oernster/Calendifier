<!--VERSION-->1.7.0<!--/VERSION-->

# Testing & Quality

How Calendifier is tested, what the coverage gate covers, how to run it and how to extend it. For build and packaging instructions see [DEVELOPMENT-README.md](DEVELOPMENT-README.md).

## Philosophy

- **100% coverage gate on the core logic surface.** The non-fragile, mock-free "core logic" of the app is held at 100% line and branch coverage. The build fails below it (`--cov-fail-under=100`).
- **No mocks.** Tests use real objects and real inputs only: temporary files, environment variables (via pytest `monkeypatch`) and the real `holidays` library. Genuinely unreachable defensive branches carry a justified `# pragma: no cover` / `# pragma: no branch` rather than a contrived test.
- **Fragile tests are isolated.** Qt/UI tests run against a real headless `QApplication` and live in `tests/ui`, outside the gate, so the gate stays fast and deterministic.
- **Determinism over ambient state.** A test must not depend on the host's environment. Anything environment-sensitive (locale, timezone) is set explicitly in the test, never inherited from the shell.

## Running the tests

The gate is configured entirely in [pyproject.toml](pyproject.toml) and [.coveragerc](.coveragerc), so every `--cov` form below resolves to the same scoped 100% gate:

```bash
# Core unit suite with the 100% coverage gate (the canonical command)
python -m pytest

# All of these are equivalent now that the scope lives in config:
python -m pytest --cov
python -m pytest -v --cov

# Qt/UI suite: real PySide6 widgets, headless, kept OUT of the gate
python -m pytest tests/ui --no-cov -o addopts=""
```

Trust the exit code, not the printed text. With a coverage gate, pytest prints the coverage table last and emits no "N passed" summary in the usual place, so a substring grep for `passed`/`failed` can match coverage filenames. `0` means tests passed and the gate was met; non-zero means read the actual failure.

## What the gate covers

The gated source set is the mock-free core logic, declared once as `[run] include` in [.coveragerc](.coveragerc):

| Module | Responsibility |
|--------|----------------|
| `version.py` | Version reading and app metadata |
| `stamp_version.py` | Stamping `VERSION` into static docs |
| `calendar_app/shared/resources.py` | Icon and resource path resolution |
| `calendar_app/data/models.py` | Domain data models |
| `calendar_app/config/settings.py` | Settings manager and holiday-country resolution |
| `calendar_app/localization/locale_detector.py` | Locale detection and normalisation |
| `calendar_app/localization/number_formatter.py` | Locale-aware number formatting |
| `calendar_app/core/rrule_parser.py` | Recurring-event RRULE parsing |
| `calendar_app/core/holiday_translations.py` | Holiday-name translation |
| `calendar_app/core/multi_country_holiday_provider.py` | Multi-country holiday provider |
| `calendar_app/core/observances.py` | Observance date engine (fixed / weekday / Easter rules) |
| `calendar_app/core/observance_data.py` | Per-country observance data and accessors |

The matching unit tests live in `tests/unit/` (`test_<module>.py`).

## Why the scope lives in `.coveragerc`, not in `--cov` flags

The scope is defined by `[run] include` in [.coveragerc](.coveragerc) and `addopts` in [pyproject.toml](pyproject.toml) carries a single bare `--cov`. This is deliberate.

The earlier setup encoded the scope as ten `--cov=<module>` flags inside `addopts`. A bare `--cov` typed on the command line (for example `pytest -v --cov`) then silently widened measurement to the whole tree, which pulled in ungated UI/NTP modules and PySide6's deploy files (`shibokensupport`, `pyscript`) and dropped the reported total below 100%. Defining the scope as a config invariant means no invocation can broaden it: the gate is the same whether `--cov` comes from `addopts` or the command line.

This is the "constrain the bad state, do not monitor for it" rule applied to the test harness.

## What is out of the gate, by design

The PySide6 UI, the NTP/network paths, the FastAPI/Home-Assistant server, the i18n manager, the bespoke installer and the build scripts are intentionally outside the primary gate. They are exercised by the Qt/UI suite, by manual run-throughs or are pure I/O glue. Keeping them out keeps the gate fast, deterministic and mock-free.

## Lint and format

The whole codebase is `black`- and `flake8`-clean. Lint settings are in [.flake8](.flake8); `black` uses line length 88.

```bash
python -m black --check .
python -m flake8 .
```

Warnings are fixed at source, never suppressed. Deprecated platform/library calls were replaced (for example `locale.getdefaultlocale` became `get_environment_locale`, and `holidays.UK(state=)` became `subdiv=`).

## Adding a module to the gate

1. Write the unit test in `tests/unit/test_<module>.py` using real objects and inputs (no mocks).
2. Add the module's file path to `[run] include` in [.coveragerc](.coveragerc).
3. Run `python -m pytest`; the run fails until that module is at 100%.

## Keeping tests deterministic

A test must produce the same result on any host. The worked example is `locale_detector.detect_system_locale()`, which reads `LANG`/`LC_ALL`. Its test sets `LANG` explicitly with `monkeypatch.setenv` and deletes the competing variables, so the environment-variable detection path is always exercised regardless of the developer's shell. Without that, the line was covered on shells that happen to set `LANG` (Git Bash) and uncovered on those that do not (a bare Windows PowerShell venv), making the gate pass or fail by accident.

The same rule applies to time: never read the wall clock in code under the gate; inject it.

## Structural tests

Beyond coverage, [tests/unit/test_structural.py](tests/unit/test_structural.py) enforces a module-size limit: every source module under `calendar_app/` (plus the root modules) must stay within 400 lines, so logic stays decomposed. Two narrow escape hatches:

- **Data modules** (pure lookup tables such as `observance_data.py`) are listed in `_DATA_MODULES` and exempt, because line count there reflects data volume, not complexity.
- **Pre-existing oversized modules** are listed in `_LEGACY_OVER_LIMIT` as tracked technical debt. This set is a ratchet: a second test fails if any entry has dropped to within the limit (or been deleted) without being removed from the list, so the debt can only shrink. New modules get no such exemption.

These tests live in `tests/unit/` so they run with every `pytest`, but they read source files rather than importing them, so they do not affect coverage.

## Troubleshooting

- **Coverage looks like 73% with `Couldn't parse / No source for code` warnings about `shibokensupport` or `pyscript`.** That was the old behaviour of a bare command-line `--cov` widening the scope. It is fixed: the scope is now a config invariant. Pull the latest [.coveragerc](.coveragerc) and [pyproject.toml](pyproject.toml).
- **A line is covered locally but reported missing on another machine.** It depends on ambient environment. Set the relevant variable in the test (see "Keeping tests deterministic").
- **The venv `python` shim fails to start.** If the venv interpreter is broken, run the suite against the venv's installed packages directly, for example:
  ```bash
  PYTHONUTF8=1 PYTHONPATH="$(pwd)/venv/Lib/site-packages:$(pwd)" py -3 -m pytest
  ```
