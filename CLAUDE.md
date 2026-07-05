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

## Linking work to Notion tickets
When a task originates from a Notion ticket, include its Ticket ID in the branch name and PR title, e.g. branch feature/TCK-3-priority-level-field, PR title "[TCK-3] Add priority_level field to res.partner". This is how merged PRs get linked back to Notion automatically.

## Working a ticket -- always start with requirements analysis
When asked to work on a ticket (e.g. "work on ticket TCK-N"), always apply ticket-requirements-analyst first. Do not write code until a PRD exists and its Review status is Approved. Only then apply odoo-module-dev, followed by qa-edge-case-tester, followed by the PR/merge/notion-ticket-sync flow already defined.

## Documentation standard for future analysis
Everything written to Notion (ticket bodies, PRDs, Release Notes) should assume it will be read and analyzed later without this conversation's context. This means:
- Always link to real Notion pages/records referenced, never just name them in prose.
- Always record explicit human decisions (not just proposed defaults that were silently accepted) as their own visible entry, not folded invisibly into other text.
- Prefer structured headings over freeform paragraphs, so future analysis (by a human or an AI) can reliably find "what was decided," "what was tested," "what shipped" without re-reading everything.
- When in doubt about whether something is worth writing down, write it down -- the cost of over-documenting a ticket is small; the cost of an undocumented decision six months from now is not.

## Ticket activity logging
Any skill that changes a ticket's Status must: (1) add a dated comment to the ticket page explaining the change, and (2) set the corresponding milestone date property on the Tickets database if one exists (Date PRD drafted, Date approved, Date in progress, Date shipped). This applies to odoo-module-dev, qa-edge-case-tester, notion-ticket-sync, and ticket-requirements-analyst alike -- log at every status transition, not just at the end.

## Token efficiency is a standing priority, for every skill
- Prefer a small, maintained reference/index over re-deriving the same information from scratch repeatedly (grepping the whole codebase, reading every historical record). If something is being re-derived often and no reference exists for it, create one and keep it updated -- don't just note the inefficiency and move on.
- When querying Notion, always filter (by relation, by tag, by property) rather than pulling entire databases. Only fetch full page content for rows that actually matched a filter.
- Local files are cheaper to read than MCP round-trips where either would work -- prefer a local index over a Notion query when the same information is available both places.
- Don't re-read something already established earlier in the same session.

## What needs a PR vs. what can push directly to master
Code changes (anything in addons/, docker-compose.yml, odoo.conf) always go through a branch + PR + review, no exceptions.
Pure documentation/context files that don't affect the running application (.claude/context/*, CLAUDE.md itself, skill files) can be committed and pushed directly to master. Still show the human the diff before pushing, since accuracy is the only thing being checked -- but a full PR cycle for a documentation correction is unnecessary ceremony.

## Notion content formatting: use real line breaks, guard against auto-links
When writing markdown content to Notion pages (PRDs, Release Notes, ticket bodies), use actual newline characters between blocks/paragraphs -- never rely on literal "\n" escape sequences embedded in a single string, since this has been observed to render as a literal "n" character instead of a line break. Write multi-paragraph content as genuinely separate lines, or use multiple smaller content insertions if unsure.

Wrap filenames, code, and anything containing a dot followed by letters (e.g. test_file.py) in inline code backticks. Notion's link auto-detection will otherwise turn bare filenames into unwanted hyperlinks (e.g. "urgent.py" became a link to a nonexistent "urgent.py" domain).

After writing any substantial content block to Notion, fetch the page back once to confirm it rendered as intended before moving on -- catching a formatting bug immediately is far cheaper than discovering five broken pages later.
