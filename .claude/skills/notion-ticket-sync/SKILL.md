---
name: notion-ticket-sync
description: Use after a PR is merged, when the PR is linked to a Notion ticket (Ticket ID like TCK-N appears in the branch name, PR title, or PR body) -- writes a Release Notes entry and marks the ticket Shipped.
---

# Notion ticket sync

## When to run this
After merging a PR, check whether the branch name, PR title, or PR body contains a Ticket ID matching the pattern TCK-<number> (e.g. TCK-3). This is how work is linked back to its originating Notion ticket.

If no Ticket ID is present anywhere: skip this whole skill and tell the human the PR wasn't linked to a ticket, so Notion won't be updated automatically.

## Step 1: find the ticket
Using the notion MCP server (never claude.ai Notion), query the Tickets database under Solopreneur Ops for the row whose Ticket ID property matches. Read its Project relation while you're there -- you'll need it for the Release Notes entry.

## Step 2: create the Release Notes entry
Create a new row in the Release Notes & Feature Log database with:
- Feature: a short human-readable name (use the PR title if it's already descriptive)
- Project: same Project as the ticket (copy the relation)
- Ticket: relation to the ticket found in Step 1
- PR link: the GitHub PR URL
- Date shipped: today's date
- Test summary: copied from the PR description's "Test summary" section, verbatim
- Edge cases found: copied from the PR description's "Edge cases found" section, verbatim
- Delivered: checked

Never paraphrase or shorten the Test summary / Edge cases found content -- copy it exactly, since it's already written for a human reader.

## Step 3: update the ticket
Set the ticket's Status to Shipped. Do not change any other ticket property.

## Step 4: confirm back to the human
State plainly: which ticket was updated, and a link to the new Release Notes row (or its title, if a direct link isn't available).

## If anything is ambiguous
If more than one ticket matches, or the Project relation is missing/unclear, stop and ask the human rather than guessing which record to update.

## Never create new Clients or Projects silently
If a ticket has no Project relation set, stop and ask the human which existing Project it belongs to, or whether a new one should be created. Never create a new Project or Client record without explicit confirmation.

## Client and Project linking, not just creation
The "never create silently" rule also covers *linking* decisions, not just brand-new records. If a Project's Client relation is empty, or a new Client/Project had to be created to satisfy a relation, stop and ask the human which existing record to link (list the options found) or confirm before creating a new one. Do not pick automatically, even when there's only one plausible existing candidate.

## Populate GitHub repo on Project creation
When creating or linking a Project, also set its "GitHub repo" property to the repo's URL if known (e.g. from the current git remote). Never leave it blank if the information is available.

## Also notify the project's Slack channel
After updating the Release Notes entry and ticket Status, look up the ticket's Project record and read its "Slack channel" property. If present, post a short message there via chat.postMessage (SLACK_BOT_TOKEN env var) summarizing what shipped, with the PR link. If the Project has no Slack channel set, skip this step silently -- don't treat it as an error.

## Tag every Release Notes entry with what it touched
When creating a Release Notes entry, always set "Odoo models/modules touched" to the actual Odoo model(s) (e.g. res.partner, sale.order) and/or addon technical name(s) the change affected. This is required, not optional -- it's what makes future context-checking cheap instead of requiring every entry to be read in full.

## Release Notes structure: minimal properties, content in the page body
The Release Notes & Feature Log database only has Feature, Project, Ticket, PR link, Odoo models/modules touched, Delivered, Date shipped as properties. Test summary and Edge cases found go into the page body as markdown headers (## Test summary, ## Edge cases found), copied verbatim from the PR description as before -- not as database properties.

## Include brief UI testing steps in Release Notes
Add a third body section, "## How to test in the UI", copied/adapted from the PR's "How to verify manually" section. Keep it brief -- a short numbered list only (e.g. "1. Open Contacts, click any record. 2. Confirm the 'Priority Level' dropdown appears next to Priority Client, defaulting to Medium."). No prose, no restating the technical implementation -- just the concrete clicks/checks a human needs to visually confirm the feature works.
