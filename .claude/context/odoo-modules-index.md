# Odoo modules index

One row per shipped module. This is the FIRST thing to check for "what already exists" -- read this before grepping addons/ or querying Notion Release Notes. Only fall back to a full grep/query if this index doesn't answer the question or seems out of date.

| Module | Model(s) touched | What it does | Ticket | Notion Release Note | Notes/quirks |
|---|---|---|---|---|---|
| custom_contact_notes | res.partner | Adds vip_notes text field, shown as tab | (pre-ticket) | (link) | |
| partner_priority_client | res.partner | Adds is_priority_client boolean, priority_level selection | (pre-ticket) | (link) | Required field on upgrade auto-backfills default |
| partner_urgency_flag | res.partner | Adds is_urgent boolean flag | TCK-2 | https://app.notion.com/p/Add-urgency-flag-to-Contacts-3948a366581581d58184fc01a1c44ed4 | |
| partner_contact_preference | res.partner | Adds preferred contact channel field (contact_preference selection) | TCK-3 | https://app.notion.com/p/Add-contact_preference-field-to-res-partner-3948a366581581538b26ebd7641c156a | Writing any res.partner field requires the Contact Creation group (base.group_partner_manager), not just base.group_user -- pre-existing, unrelated to this field (see TCK-4) |
| project_sale_order_ux | project.project | Reorders Projects app to default List view; adds a Project -> Sales Order smart button (reuses core sale_project's sale_order_id field, no new field) | TCK-5 | https://app.notion.com/p/Default-Projects-list-view-Project-Sales-Order-smart-button-3948a3665815816da270d57fe95c1136 | Button gated to sales_team.group_sale_salesman -- a plain project user without Sales access would otherwise hit an AccessError opening the linked sale.order |
| project_type_field | project.project | Adds project_type selection field (Permanent / SPAA) | TCK-6 | https://app.notion.com/p/Add-Project-Type-field-to-Projects-3948a366581581faa5e8f420715534d7 | required="1" in the form view only, NOT required=True at the model/DB level -- a hard DB-level required would break sale_project's automatic project creation on Sales Order confirmation and project_sale_order_ux's tests. Existing projects backfilled to "Permanent" via post_init_hook. |
