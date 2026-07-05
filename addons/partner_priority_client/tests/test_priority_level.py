import psycopg2

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestPriorityLevel(TransactionCase):
    def test_default_is_medium(self):
        partner = self.env["res.partner"].create({"name": "Default Priority Co"})
        self.assertEqual(partner.priority_level, "medium")

    def test_explicit_values_accepted(self):
        for value in ("low", "medium", "high"):
            partner = self.env["res.partner"].create(
                {"name": f"{value} priority Co", "priority_level": value}
            )
            self.assertEqual(partner.priority_level, value)

    def test_invalid_value_rejected(self):
        with self.assertRaises(ValueError):
            self.env["res.partner"].create(
                {"name": "Bad Priority Co", "priority_level": "urgent"}
            )

    @mute_logger("odoo.sql_db")
    def test_field_cannot_be_null_at_db_level(self):
        partner = self.env["res.partner"].create({"name": "Null Priority Co"})
        with self.assertRaises(psycopg2.Error):
            with self.cr.savepoint():
                self.env.cr.execute(
                    "UPDATE res_partner SET priority_level = NULL WHERE id = %s",
                    (partner.id,),
                )

    def test_existing_partner_backfilled_on_write(self):
        # Simulates a pre-existing record written via the ORM without
        # specifying priority_level explicitly -- should still get the default.
        partner = self.env["res.partner"].create({"name": "Backfill Co"})
        partner.write({"name": "Backfill Co Renamed"})
        self.assertEqual(partner.priority_level, "medium")
