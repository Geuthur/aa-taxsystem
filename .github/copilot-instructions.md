````instructions
# GitHub Copilot Instructions for aa-taxsystem

## Purpose
Help AI coding agents become immediately productive in this repository by documenting the app's architecture, developer workflows, conventions, and key integration points.

## Commit Message Format (preserved)
All commit messages must start with one of these prefixes:
- `[ADD]`, `[CHANGE]`, `[FIX]`, `[REMOVE]`

Example:
```
[FIX] resolve division by zero error in tax calculations
Details: why, what, notes for reviewers
```

## Big-picture architecture (quick)
- This package implements the Django app `taxsystem/` — the core of the AA Tax System.
- Background workers: Celery tasks defined in `taxsystem/tasks.py` (e.g. `update_all_taxsytem`, `update_corporation`). These use AllianceAuth's `QueueOnce` and `allianceauth.services.tasks` patterns to avoid duplicate work.
- Configuration: `taxsystem/app_settings.py` exposes settings like `TAXSYSTEM_BULK_BATCH_SIZE` and `TAXSYSTEM_STALE_TYPES` which callers may override in `local.py`.
- Models and domain: look under `taxsystem/models/` (`corporation.py`, `alliance.py`) for owner/update manager logic.

## Key files and folders (where to look first)
- `taxsystem/` — main app source (models, views, tasks, templates, static, locale)
- `taxsystem/tasks.py` — celery tasks and task defaults
- `taxsystem/app_settings.py` — default runtime tunables
- `runtests.py` — test entrypoint; sets `DJANGO_SETTINGS_MODULE` to `testauth.settings.local`
- `Makefile` + `.make/conf.d/tests.mk` — common developer commands (`make coverage`, `make build-test`)
- `docs/` and `taxsystem/docs/` — user and developer documentation and design notes
 - `.github/PULL_REQUEST_TEMPLATE.md` — PR template and checklist used for contributions

## Developer workflows & commands (concrete)
- Run unit tests quickly (uses local `testauth` fixture):
	- `python runtests.py` (invokes Django test runner via `testauth.settings.local`)
- Run coverage and HTML report:
	- `make coverage` (requires an active virtualenv)
- Build package for release or tests:
	- `make build-test` (calls `python3 -m build`)
- Migrations & collectstatic (when deploying into an AA instance):
	- `python manage.py collectstatic` and `python manage.py migrate` in your Alliance Auth project
- Scheduled task to run in production: set `CELERYBEAT_SCHEDULE` to call `taxsystem.tasks.update_all_taxsytem` (see README example)

## Conventions & patterns unique to this repo
- Tasks: All Celery tasks use `TASK_DEFAULTS` in `taxsystem/tasks.py` and often the `QueueOnce` base to avoid duplicates.
- Update flow: owner-level `update_manager` decides which `update_*` sections run; tasks call owner methods via reflection (`getattr`) — follow existing `update_*` naming when adding new sections.
- Settings: prefer adding defaults to `taxsystem/app_settings.py` and allow overrides via `local.py` (do not hardcode environment-specific values).
- Bulk DB operations: respect `TAXSYSTEM_BULK_BATCH_SIZE` to avoid large transactions.

## Integration points / external dependencies
- Alliance Auth: this app integrates tightly with Alliance Auth extension points (`allianceauth.services.hooks`, `allianceauth.services.tasks`). Use the same logger pattern: `get_extension_logger` + `LoggerAddTag`.
- Celery: tasks must be idempotent and respect time limits (`TAXSYSTEM_TASKS_TIME_LIMIT`).
- Translations: `taxsystem/locale/` contains `.po` files; use `django-admin makemessages` / `compilemessages` per repo Makefile conventions.

## Tests and test harness specifics
- Tests run against a local test Django project in `testauth/`; `runtests.py` sets `DJANGO_SETTINGS_MODULE` accordingly. Use `--keepdb` in CI to speed runs when appropriate.
- See `.make/conf.d/tests.mk` for the `coverage` target used in CI.

## What reviewers/agents should avoid changing
- Do not change the task naming conventions or the `QueueOnce` usage without ensuring backward compatibility with Celery scheduling and once-only semantics.
- Avoid altering `TAXSYSTEM_*` default keys in `app_settings.py` without documenting migration or rollout steps.

If any section is unclear or you want more examples (for instance, a short walkthrough of adding a new `update_*` section), tell me which area and I'll expand with concrete code snippets.
## Pre-PR checks (must do before opening a PR)
- Always run the test coverage target inside the project's virtual environment before creating a PR.

Typical steps (example environment used by CI/deployments for this repo):

```bash
# Activate the virtualenv used for tests
# (example) activate the virtualenv used for tests — replace with your own venv
# A Fully installed ([AA Dev Environment](https://allianceauth.readthedocs.io/en/latest/development/dev_setup/aa-dev-setup-wsl-vsc-v2.html)) is assumed here 
source /home/testauth/venv/bin/activate

# Change into the repository (or use ../auth if you have a symlink)
cd /home/github/aa-taxsystem

# Run the coverage target (Makefile target)
make coverage
```

If any section is unclear or you want more examples (for instance, a short walkthrough of adding a new `update_*` section), tell me which area and I'll expand with concrete code snippets.
````