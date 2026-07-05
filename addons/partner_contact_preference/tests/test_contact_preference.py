from odoo.tests.common import TransactionCase


class TestContactPreference(TransactionCase):
    def test_default_is_empty(self):
        partner = self.env["res.partner"].create({"name": "Default Preference Co"})
        self.assertFalse(partner.contact_preference)

    def test_explicit_values_accepted(self):
        for value in ("email", "phone", "sms", "whatsapp", "mail"):
            partner = self.env["res.partner"].create(
                {"name": f"{value} preference Co", "contact_preference": value}
            )
            self.assertEqual(partner.contact_preference, value)

    def test_invalid_value_rejected(self):
        with self.assertRaises(ValueError):
            self.env["res.partner"].create(
                {
                    "name": "Bad Preference Co",
                    "contact_preference": "carrier_pigeon",
                }
            )

    def test_preference_can_be_changed(self):
        partner = self.env["res.partner"].create(
            {"name": "Change Preference Co", "contact_preference": "email"}
        )
        partner.write({"contact_preference": "phone"})
        self.assertEqual(partner.contact_preference, "phone")

    def test_preference_can_be_cleared(self):
        partner = self.env["res.partner"].create(
            {"name": "Clear Preference Co", "contact_preference": "email"}
        )
        partner.write({"contact_preference": False})
        self.assertFalse(partner.contact_preference)

    def test_no_db_level_constraint_on_raw_sql_write(self):
        # Unlike a required Selection field (e.g. priority_level in
        # partner_priority_client, which is NOT NULL), an optional Selection
        # field has no DB-level CHECK constraint -- enum validation is
        # ORM-level only (see test_invalid_value_rejected above). A raw SQL
        # write bypassing the ORM succeeds; this is standard Odoo behavior
        # for optional Selection fields, not a gap introduced here.
        partner = self.env["res.partner"].create({"name": "DB Bypass Co"})
        self.env.cr.execute(
            "UPDATE res_partner SET contact_preference = %s WHERE id = %s",
            ("carrier_pigeon", partner.id),
        )
        partner.invalidate_recordset()
        self.env.cr.execute(
            "SELECT contact_preference FROM res_partner WHERE id = %s",
            (partner.id,),
        )
        self.assertEqual(self.env.cr.fetchone()[0], "carrier_pigeon")

    def test_user_with_contact_write_rights_can_read_and_write(self):
        # Plain internal users (base.group_user only) cannot write to any
        # res.partner field in this instance -- write access requires the
        # "Contact Creation" group (base.group_partner_manager) or an
        # administrator group. That's pre-existing base/Contacts access
        # control, unrelated to this field. This test confirms the new
        # field behaves like any other partner field for a user who *does*
        # have contact-write rights, rather than asserting the (incorrect)
        # premise that any internal user can write to Contacts.
        contact_manager = self.env["res.users"].create(
            {
                "name": "Contact Manager User",
                "login": "contact_manager_user_contact_pref",
                "groups_id": [
                    (6, 0, [self.env.ref("base.group_partner_manager").id])
                ],
            }
        )
        partner = self.env["res.partner"].create(
            {"name": "Access Rights Co", "contact_preference": "phone"}
        )
        partner_as_user = partner.with_user(contact_manager)
        self.assertEqual(partner_as_user.contact_preference, "phone")
        partner_as_user.write({"contact_preference": "whatsapp"})
        self.assertEqual(partner.contact_preference, "whatsapp")
