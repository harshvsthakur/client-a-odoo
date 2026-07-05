---
name: ticket-requirements-analyst
description: Use whenever asked to "work on ticket TCK-N" -- ALWAYS run this before writing any code. Acts as a product manager / implementation consultant to check requirements are clear, review what's already built, and draft a PRD for human approval before any build work starts.
---

# Ticket requirements analysis

Never jump straight to writing code from a ticket. This skill is the mandatory step in between.

## Step 1: read the ticket fully
Using the notion MCP server, fetch the ticket from the Tickets database, its Project, and check whether a PRD already exists and is Approved (if so, skip to step 6).

## Step 2: assess whether the ticket is actually clear enough to build
Check for: which model(s) are affected, what the field/feature should actually do, any acceptance criteria, and any implied UI location. A one-line ticket like "add a priority field" is NOT enough on its own -- infer sensible defaults where genuinely unambiguous (e.g. field type from context), but flag anything that's a real judgment call rather than silently deciding it yourself.

## Step 3: check what's already built
- Search addons/ for existing modules touching the same model(s) -- don't propose something that already exists or conflicts with it.
- Query the Release Notes & Feature Log database for this Project to see what's already shipped -- check for overlapping or conflicting prior features.
- If this ticket would conflict with, duplicate, or need to extend already-delivered work, say so explicitly in the PRD.

## Step 4: understand the workflow impact
Think through how this fits into how the model/feature is actually used day to day -- not just "does the field exist" but "does this make sense given how someone would use Contacts/Sales/etc. in practice." Note anything that seems like it'll create an awkward or confusing user experience.

## Step 5: draft the PRD
Create a row in the PRDs & DevOps Plans database, linked to the ticket, with:
- Requirements summary: a clear, complete restatement of what's being built, including anything you inferred
- Existing customizations checked: what you found in addons/ and Release Notes, and how this relates to it
- Technical approach: model(s), field(s)/view(s) affected, brief implementation plan
- Risks / open questions: anything genuinely ambiguous, any judgment calls you made, anything you'd want a human to confirm before building

Set the PRD's Review status to "Needs your review". Set the ticket's Status to "PRD drafted".

## Step 6: stop
Do not proceed to writing any code. Tell the human the PRD is ready for review and where to find it. Wait for explicit approval (the PRD's Review status set to Approved, or the human saying so directly) before applying odoo-module-dev or any other build skill.

## If the ticket is genuinely too vague to draft a reasonable PRD
Don't guess wildly to fill gaps. List the specific missing information as questions in the PRD's "Risks / open questions" field, set Review status to "Needs your review", and stop -- the human will either answer inline or update the ticket.

## Also write the summary into the ticket's own page body
In addition to creating the linked PRD database row, write a concise summary directly into the Ticket page's content (not just its properties) using these headings:

### Requirements
What's being built, in plain language, including anything inferred.

### What's already built (context checked)
Relevant existing modules/features found in addons/ and Release Notes, and how this relates to them.

### Open questions
Anything genuinely ambiguous that needs human input before building -- omit this heading entirely if there are none.

Append this under the ticket's existing content rather than replacing anything already there. This makes the ticket readable on its own, without requiring someone to open the linked PRD record to understand the plan.
