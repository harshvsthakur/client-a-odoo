from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestProjectSaleOrderUx(TransactionCase):
    def _create_project_with_sale_order(self):
        partner = self.env["res.partner"].create({"name": "SO UX Customer"})
        product = self.env["product.product"].create(
            {"name": "SO UX Service", "type": "service", "invoice_policy": "order"}
        )
        order = self.env["sale.order"].create({"partner_id": partner.id})
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": product.id,
                "product_uom_qty": 1,
            }
        )
        project = self.env["project.project"].create(
            {
                "name": "SO UX Project",
                "partner_id": partner.id,
                "allow_billable": True,
                "sale_line_id": line.id,
            }
        )
        return project, order

    def test_sale_order_id_populated_from_sale_line(self):
        project, order = self._create_project_with_sale_order()
        self.assertEqual(project.sale_order_id, order)

    def test_action_view_sale_order_ux_returns_correct_order(self):
        project, order = self._create_project_with_sale_order()
        action = project.action_view_sale_order_ux()
        self.assertEqual(action["res_model"], "sale.order")
        self.assertEqual(action["res_id"], order.id)
        self.assertEqual(action["view_mode"], "form")

    def test_action_view_sale_order_ux_without_order_raises(self):
        project = self.env["project.project"].create({"name": "No SO Project"})
        self.assertFalse(project.sale_order_id)
        with self.assertRaises(UserError):
            project.action_view_sale_order_ux()

    def test_action_view_sale_order_ux_requires_single_record(self):
        project_a, _order_a = self._create_project_with_sale_order()
        project_b, _order_b = self._create_project_with_sale_order()
        projects = project_a + project_b
        with self.assertRaises(ValueError):
            projects.action_view_sale_order_ux()

    def test_projects_action_defaults_to_list_view(self):
        action = self.env.ref("project.open_view_project_all")
        self.assertEqual(action.view_mode.split(",")[0], "list")

    def test_sales_user_can_open_the_linked_order(self):
        # A user with Sales access (the group the button is gated to) should
        # be able to follow through and actually read the linked order --
        # unlike a plain project-only user, who cannot (see PR description).
        sales_user = self.env["res.users"].create(
            {
                "name": "Sales User Probe",
                "login": "sales_user_probe_contact_pref",
                "groups_id": [
                    (6, 0, [self.env.ref("sales_team.group_sale_salesman").id])
                ],
            }
        )
        project, order = self._create_project_with_sale_order()
        action = project.with_user(sales_user).action_view_sale_order_ux()
        order_as_user = (
            self.env["sale.order"].with_user(sales_user).browse(action["res_id"])
        )
        self.assertEqual(order_as_user, order)
