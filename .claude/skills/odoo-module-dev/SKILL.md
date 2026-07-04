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
