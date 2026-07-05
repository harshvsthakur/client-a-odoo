# Odoo modules index

One row per shipped module. This is the FIRST thing to check for "what already exists" -- read this before grepping addons/ or querying Notion Release Notes. Only fall back to a full grep/query if this index doesn't answer the question or seems out of date.

| Module | Model(s) touched | What it does | Ticket | Notion Release Note | Notes/quirks |
|---|---|---|---|---|---|
| custom_contact_notes | res.partner | Adds vip_notes text field, shown as tab | TCK-1 (pre-ticket) | (link) | |
| partner_priority_client | res.partner | Adds is_priority_client boolean, priority_level selection | TCK-2 | (link) | Required field on upgrade auto-backfills default |
| partner_contact_preference | res.partner | Adds preferred contact channel field | TCK-3 | (link) | |
