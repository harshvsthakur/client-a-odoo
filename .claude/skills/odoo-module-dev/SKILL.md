---
name: odoo-module-dev
description: Use whenever writing, modifying, or reviewing custom Odoo modules in this repo's addons/ folder — covers module structure, coding conventions, and the git/PR workflow to follow after code is written.
---

# Odoo module development conventions

## Before writing any code
- Check `addons/` for existing modules that might already cover this, or that this new work should extend rather than duplicate.
- Confirm which Odoo model(s) are involved and whether they're core, or already customized by an existing module here.

## Module structure
- One feature/concern per module where reasonable — don't pile unrelated changes into one addon.
- Every module needs: `__manifest__.py` (name, version matching Odoo 18.0.x.y.z, depends, data files listed), `__init__.py` importing `models`, a `models/` folder with matching `__init__.py`.
- Inherit existing models with `_inherit`, never modify core Odoo files directly.
- View changes go in `views/`, use `<xpath>` or field-relative `position` inheritance, not full view replacement, unless truly necessary.

## After code is written — do this automatically, don't wait to be asked
1. Create a new branch: `git checkout -b feature/<short-description>`
2. Commit with a clear, specific message describing what changed and why (not just "update module").
3. Push the branch: `git push -u origin feature/<short-description>`
4. Open a PR with `gh pr create`, with a description covering: what changed, which model/view it touches, and how to verify it manually (exact steps, e.g. which menu/field to check in the UI).
5. Do not merge the PR yourself — leave it open for human review.

## Testing before opening the PR
- Where practical, install/update the module in the running dev database and confirm it loads without errors before pushing (`docker compose exec odoo odoo -i <module> -d harsh-test --stop-after-init`, then `docker compose restart odoo`).
- Note any manual verification steps you weren't able to run yourself in the PR description, so the reviewer knows what to check.

## When told to merge a PR
Once a human says something like "merge PR #N" or "approved, merge it":
1. `gh pr merge <N> --merge`
2. `git checkout master && git pull`
3. Update the module(s) in the dev database: `docker compose exec odoo odoo -u <module_name(s)> -d harsh-test --stop-after-init`
4. `docker compose restart odoo`
5. Confirm back to the human that it's live and ready for browser verification, and remind them to hard-refresh (Ctrl+Shift+R) since Odoo's asset bundles are cached aggressively.
Never merge without an explicit human instruction to do so.

## After merging, sync to Notion
Once the merge-and-deploy sequence above completes, also apply the notion-ticket-sync skill if the PR is linked to a Ticket ID.

## Check for technical naming conflicts before writing code
Before adding a new field or view to an existing model, grep addons/ for the exact field name and any XML record IDs you're about to introduce, on that same model. If something already uses the same name, either reuse/extend it (per the "check for existing customizations" step) or pick a distinctly different name -- don't rely on the install step to be the first thing that catches a collision.

## Keep the local index current
After a module ships (PR merged), add or update its row in .claude/context/odoo-modules-index.md -- module name, model(s) touched, what it does, ticket, Release Note link, any quirks worth remembering (like permission requirements discovered). This is a required step, not optional -- it's what keeps future context-checking cheap. Commit this file alongside the code.
