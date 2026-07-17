# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository. Process-level conventions (Notion workflow, PR policy, documentation standards, token
efficiency, activity logging) live in the global `~/.claude/CLAUDE.md` and apply here unchanged --
this file only covers what's specific to this project.

## Project overview

This repo is a Docker-based runtime environment for Odoo 18.0 (Community edition). It currently
contains no custom addons — `addons/` is empty and is where custom Odoo modules should be placed
as they are developed. There is no application code yet; the repo is infrastructure/config only.

## Architecture

- `docker-compose.yml` defines two services:
  - `db` — Postgres 16, credentials `odoo`/`odoo`, data persisted in the `db-data` volume.
  - `odoo` — official `odoo:18.0` image, depends on `db`, exposed on host port `8069`.
- `odoo.conf` is bind-mounted into the container at `/etc/odoo/odoo.conf`. Its `addons_path`
  includes both `/mnt/extra-addons` (mapped from local `./addons`) and Odoo's built-in addons
  path. Any custom module placed in `./addons/<module_name>/` becomes available to Odoo without
  further config changes.
- `./addons` is bind-mounted to `/mnt/extra-addons` in the container — this is the sole
  integration point between this repo and custom module code.
- Odoo application data (filestore, sessions) persists in the `odoo-data` named volume, separate
  from the addons source in this repo.

## Common commands

```bash
# Start the stack (Postgres + Odoo) in the background
docker compose up -d

# Follow Odoo logs
docker compose logs -f odoo

# Stop the stack
docker compose down

# Restart Odoo only (e.g. after adding/updating an addon) with module upgrade
docker compose exec odoo odoo -u <module_name> -d <database_name> --stop-after-init
docker compose restart odoo

# Open a shell inside the Odoo container
docker compose exec odoo bash
```

Odoo is reachable at `http://localhost:8069` once the stack is up; the first run prompts for
database creation through the web UI.

## Notes for adding custom modules

- New addons go under `addons/<module_name>/` with a standard Odoo module layout
  (`__manifest__.py`, `models/`, `views/`, etc.) — no changes to `odoo.conf` or
  `docker-compose.yml` are needed for a new module to be picked up.
- After adding or changing a module, upgrade/install it with `-u`/`-i` as shown above, or use
  Odoo's Apps UI, then restart the `odoo` service so changes take effect.

## Testing

Dev database: `harsh-test`. Command patterns (test run, manual REPL, test file conventions) come from the `odoo-conventions:odoo-module-dev` skill (the shared `odoo-conventions` plugin) -- substitute `harsh-test` for its `<dev_database>` placeholder.

## Codebase conventions

- Existing customizations: search `addons/` for the relevant Odoo model/field/view names before assuming something doesn't already exist.
- Local index: check `.claude/context/odoo-modules-index.md` first -- it tracks every shipped module, the model(s) it touches, its ticket/Release Note link, and any quirks worth remembering. Cheaper than a full `addons/` scan or a Release Notes query; only fall back to those if the index is missing, incomplete, or stale.

## What counts as code

Code (always needs a branch + PR + review, no exceptions): anything in `addons/`, `docker-compose.yml`, `odoo.conf`.

Pure documentation/context (can push directly to master, after showing the human the diff): `.claude/context/*`, this `CLAUDE.md`, skill files under `.claude/skills/`.

## Deploying an update

Dev database: `harsh-test` (same as "Testing" above). Command pattern comes from the `odoo-conventions:odoo-module-dev` skill; it also carries the cache-busting reminder (Odoo's asset bundles are cached aggressively -- hard-refresh with Ctrl+Shift+R after deploying).

## Environments

`local` only — the Docker stack on this machine (see "Deploying an update"). No staging or production exists for this project; a merged PR deployed locally is fully shipped.

## Visibility

personal — this is Harsh's own Odoo testbed ("Odoo v18 Community Test"), not a client engagement. The "client-a" name (repo and elsewhere) is **simulated** — a role-played client used to exercise the pipeline end-to-end; no real client is behind it, which is why the GitHub repo is safely public. Its shipped work may be mined for public content (LinkedIn, showcase) in full technical detail, per the global Content Pipeline ground rules.

## Ticket workflow for this project

Standard global pipeline (see "The ticket pipeline" in `~/.claude/CLAUDE.md`); this project's build skill (step 2) is `odoo-conventions:odoo-module-dev`, the shared type-tier plugin.
