# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## Notion access — scope restriction

Only use the "notion" (stdio, token-scoped) MCP server for anything Notion-related. Never use the "claude.ai Notion" connector for this project — it authenticates with full personal workspace permissions and is not scoped to this project.

Within Notion, only interact with the Tickets database under the Solopreneur Ops page (and its directly related PRDs / Release Notes / Project rows via that database's relations). Do not search, fetch, or reference any other Notion page or database, even if tools make it technically reachable.

If the "notion" stdio server is unavailable in a given session, stop and tell the human rather than falling back to the claude.ai Notion connector.
