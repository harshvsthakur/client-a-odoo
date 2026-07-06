# Odoo v18 Community Test

A Docker-based Odoo 18 (Community) environment plus custom addons — my personal testbed for an
**agentic engineering workflow**: every module in this repo was built by Claude Code driving a
full delivery pipeline (Notion ticket → PRD → code → automated tests + edge-case QA → PR →
merge → deploy → release notes), with human approval gates at the PRD and merge steps.

The repo doubles as a working example of that pipeline; the modules themselves are deliberately
small, realistic ERP customizations.

## Stack

- Odoo 18.0 Community (official image) + Postgres 16, via `docker-compose.yml`
- Custom addons in `addons/`, bind-mounted to `/mnt/extra-addons` — no config changes needed
  for a new module to be picked up

## Custom modules

| Module | What it does |
|---|---|
| `custom_contact_notes` | VIP notes text field on Contacts |
| `partner_urgency_flag` | Urgent-follow-up flag on Contacts |
| `partner_priority_client` | Priority-client checkbox + Low/Medium/High priority level on Contacts |
| `partner_contact_preference` | Contact-preference tracking on Contacts |
| `project_sale_order_ux` | Project ⇄ Sales Order smart buttons, list view as default for Projects |
| `project_type_field` | Required Permanent/SPAA project-type classification on Projects |

Each module ships with automated tests (`tests/test_*.py`, `TransactionCase`) written as part of
the pipeline's QA stage.

## Running it

```bash
docker compose up -d          # start Postgres + Odoo
# Odoo at http://localhost:8069 (first run prompts to create a database)

# install/upgrade a module, then restart
docker compose exec odoo odoo -u <module_name> -d <database_name> --stop-after-init
docker compose restart odoo
```

Note: Odoo caches asset bundles aggressively — hard-refresh (Ctrl+Shift+R) after deploying a
view change.

## How this repo is developed

Process conventions live in `CLAUDE.md` (and a shared multi-tier Claude Code setup: global
process rules → an `odoo-conventions` plugin shared across Odoo projects → this repo's own
config). All code lands via ticket-linked branches (`feature/TCK-N-*`) and PRs; tests run before
every PR; a human approves every PRD and merge.
