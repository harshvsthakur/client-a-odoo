from odoo.tests.common import TransactionCase


class TestIsUrgent(TransactionCase):
    def test_default_is_false(self):
        partner = self.env["res.partner"].create({"name": "Default Urgency Co"})
        self.assertFalse(partner.is_urgent)

    def test_explicit_true_accepted(self):
        partner = self.env["res.partner"].create(
            {"name": "Urgent Co", "is_urgent": True}
        )
        self.assertTrue(partner.is_urgent)

    def test_flag_can_be_toggled(self):
        partner = self.env["res.partner"].create(
            {"name": "Toggle Co", "is_urgent": True}
        )
        partner.write({"is_urgent": False})
        self.assertFalse(partner.is_urgent)
