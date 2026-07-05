---
name: qa-edge-case-tester
description: Use after writing or modifying an Odoo module, before opening or updating a PR -- write and run real automated tests, then actively probe edge cases to find what breaks, not just confirm the happy path works.
---

# QA and edge-case testing

Testing isn't confirming the module installs -- it's trying to break your own work before a human reviewer has to.

## Step 1: write real automated tests

- Create tests/test_<feature>.py extending odoo.tests.common.TransactionCase.
- Create tests/__init__.py importing the test file(s). Odoo auto-discovers a tests/ folder -- no manifest changes needed.
- Cover at minimum:
  - The normal/happy path.
  - Empty or False/None values on the new field(s).
  - Maximum-length or unusually long text input.
  - Special characters (quotes, HTML tags, unicode) in text fields.
  - Wrong data type or out-of-range values on numeric/selection fields.
  - Access rights: does a non-admin user hit an error they shouldn't?

## Step 2: run the tests for real

    docker compose exec odoo odoo -d harsh-test -i MODULE_NAME --test-enable --test-tags /MODULE_NAME --stop-after-init

Look for the summary line (e.g. "X tests ... OK" or a FAIL/ERROR). Never report tests as passing without having actually run this and read the output.

## Step 3: manually probe beyond what the automated tests cover

Use the Odoo shell for interactive exploration automated tests might miss:

    docker compose exec odoo odoo shell -d harsh-test

Try things like: setting the new field via write() with a deliberately malformed value, checking what happens on a record with no related data, checking concurrent edits if relevant.

## Step 4: if you find a real bug, fix it before opening the PR

Don't document a known bug as a "finding" if it's cheap to just fix. Reserve "edge cases found" for things that are genuinely out of scope, ambiguous product decisions, or worth flagging for the human to weigh in on.

## Step 5: report findings in the PR description under these exact headings

Use these two headings verbatim -- they map directly to the Notion Release Notes database fields, so they can be copied in as-is later:

Test summary: what was tested, automated + manual, pass/fail state.
Edge cases found: anything unexpected, any judgment calls made, anything the reviewer should specifically eyeball.

Never mark a PR ready for review without having completed steps 1-3 first.