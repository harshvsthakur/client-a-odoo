from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase


class TestBudgetRecognition(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.categ = cls.env.ref(
            "stock_store_production_route.product_category_production_materials"
        )
        cls.production = cls.env.ref(
            "stock_store_production_route.stock_location_production_floor"
        )
        cls.consumption = cls.env.ref(
            "stock_store_production_route.stock_location_production_consumption"
        )
        cls.pt_consume = cls.env.ref(
            "stock_store_production_route.picking_type_production_consume"
        )

        cls.vendor = cls.env["res.partner"].create({"name": "TCK10 Test Vendor"})
        cls.customer = cls.env["res.partner"].create({"name": "TCK10 Test Customer"})

        cls.material = cls.env["product.product"].create({
            "name": "TCK10 Test Material",
            "type": "consu",
            "is_storable": True,
            "categ_id": cls.categ.id,
            "standard_price": 10.0,
        })
        cls.env["stock.quant"]._update_available_quantity(cls.material, cls.production, 100.0)

        cls.service = cls.env["product.product"].create({
            "name": "TCK10 Test Service",
            "type": "service",
        })

        cls.project = cls.env["project.project"].create({"name": "TCK10 Test Project"})

        cls.sale_order = cls.env["sale.order"].create({
            "partner_id": cls.customer.id,
            "order_line": [(0, 0, {
                "product_id": cls.service.id,
                "product_uom_qty": 1,
                "price_unit": 10000.0,
            })],
        })
        cls.sale_order.action_confirm()
        # sale_order_id is a related field derived from sale_line_id -- set that instead.
        cls.project.sale_line_id = cls.sale_order.order_line[0].id

    def _confirmed_po_line(self, product, price_unit, account=None, pct=100.0):
        account = account or self.project.account_id
        po = self.env["purchase.order"].create({
            "partner_id": self.vendor.id,
            "order_line": [(0, 0, {
                "product_id": product.id,
                "product_qty": 1,
                "price_unit": price_unit,
                "analytic_distribution": {str(account.id): pct},
            })],
        })
        po.button_confirm()
        return po.order_line

    def _consume(self, quantity, project=None):
        picking = self.env["stock.picking"].create({
            "picking_type_id": self.pt_consume.id,
            "location_id": self.production.id,
            "location_dest_id": self.consumption.id,
            "project_id": project.id if project else False,
            "move_ids": [(0, 0, {
                "name": self.material.name,
                "product_id": self.material.id,
                "product_uom_qty": quantity,
                "product_uom": self.material.uom_id.id,
                "location_id": self.production.id,
                "location_dest_id": self.consumption.id,
            })],
        })
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.picked = True
        picking.button_validate()
        return picking

    def test_project_auto_provisions_analytic_account(self):
        project = self.env["project.project"].create({"name": "Auto Analytic Account"})
        self.assertTrue(project.account_id)
        self.assertEqual(project.account_id.plan_id, self.env.ref("analytic.analytic_plan_projects"))

    def test_committed_cost_counts_service_lines_only(self):
        self._confirmed_po_line(self.service, 500.0)
        self._confirmed_po_line(self.material, 300.0)  # stockable -- must be excluded
        self.project.invalidate_recordset()
        self.assertEqual(self.project.committed_cost, 500.0)

    def test_committed_cost_respects_analytic_distribution_share(self):
        self._confirmed_po_line(self.service, 1000.0, pct=40.0)
        self.project.invalidate_recordset()
        self.assertEqual(self.project.committed_cost, 400.0)

    def test_committed_cost_ignores_unconfirmed_po(self):
        po = self.env["purchase.order"].create({
            "partner_id": self.vendor.id,
            "order_line": [(0, 0, {
                "product_id": self.service.id,
                "product_qty": 1,
                "price_unit": 999.0,
                "analytic_distribution": {str(self.project.account_id.id): 100.0},
            })],
        })
        self.project.invalidate_recordset()
        self.assertEqual(self.project.committed_cost, 0.0, "draft PO must not count as committed")
        po.button_confirm()
        self.project.invalidate_recordset()
        self.assertEqual(self.project.committed_cost, 999.0)

    def test_consumption_requires_project_to_validate(self):
        picking = self.env["stock.picking"].create({
            "picking_type_id": self.pt_consume.id,
            "location_id": self.production.id,
            "location_dest_id": self.consumption.id,
            "move_ids": [(0, 0, {
                "name": self.material.name,
                "product_id": self.material.id,
                "product_uom_qty": 1.0,
                "product_uom": self.material.uom_id.id,
                "location_id": self.production.id,
                "location_dest_id": self.consumption.id,
            })],
        })
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.picked = True
        with self.assertRaises(ValidationError):
            picking.button_validate()

    def test_consumption_cost_attributed_to_project(self):
        self._consume(4.0, project=self.project)
        self.project.invalidate_recordset()
        self.assertEqual(self.project.consumption_cost, 40.0)  # 4 * standard_price 10.0

    def test_committed_and_consumption_costs_do_not_double_count(self):
        # A material PO is committed at confirmation, then the same material is consumed --
        # only consumption_cost should reflect its value; committed_cost must stay at 0 for it.
        self._confirmed_po_line(self.material, 300.0)
        self._consume(4.0, project=self.project)
        self.project.invalidate_recordset()
        self.assertEqual(self.project.committed_cost, 0.0)
        self.assertEqual(self.project.consumption_cost, 40.0)
        self.assertEqual(self.project.cost_incurred, 40.0)

    def test_percent_complete_zero_when_budget_unset(self):
        self._consume(4.0, project=self.project)
        self.project.invalidate_recordset()
        self.assertEqual(self.project.percent_complete, 0.0)

    def test_percent_complete_capped_at_100_percent(self):
        self.project.total_budgeted_cost = 10.0
        self._consume(4.0, project=self.project)  # cost_incurred = 40.0, way over budget
        self.project.invalidate_recordset()
        self.assertEqual(self.project.percent_complete, 1.0)

    def test_recognized_revenue_formula(self):
        self.project.total_budgeted_cost = 100.0
        self._confirmed_po_line(self.service, 50.0)
        self.project.invalidate_recordset()
        self.assertEqual(self.project.percent_complete, 0.5)
        self.assertEqual(self.project.recognized_revenue, 5000.0)  # 0.5 * 10000.0 SO untaxed

    def test_recognize_revenue_posts_incremental_entry(self):
        self.project.total_budgeted_cost = 100.0
        self._confirmed_po_line(self.service, 50.0)
        self.project.invalidate_recordset()
        self.project.action_recognize_revenue()
        self.assertEqual(self.project.revenue_recognized_to_date, 5000.0)

        move = self.env["account.move"].search(
            [("journal_id", "=", self.env.ref("project_budget_recognition.journal_revenue_recognition").id)],
            limit=1, order="id desc",
        )
        self.assertEqual(move.state, "posted")
        wip_account = self.env.ref("project_budget_recognition.account_unbilled_receivable_wip")
        revenue_account = self.env.ref("project_budget_recognition.account_recognized_revenue")
        debit_line = move.line_ids.filtered(lambda l: l.account_id == wip_account)
        credit_line = move.line_ids.filtered(lambda l: l.account_id == revenue_account)
        self.assertEqual(debit_line.debit, 5000.0)
        self.assertEqual(credit_line.credit, 5000.0)

    def test_recognize_revenue_idempotent_when_unchanged(self):
        self.project.total_budgeted_cost = 100.0
        self._confirmed_po_line(self.service, 50.0)
        self.project.invalidate_recordset()
        self.project.action_recognize_revenue()
        with self.assertRaises(UserError):
            self.project.action_recognize_revenue()

    def test_recognize_revenue_posts_reversal_on_downward_revision(self):
        self.project.total_budgeted_cost = 100.0
        self._confirmed_po_line(self.service, 50.0)
        self.project.invalidate_recordset()
        self.project.action_recognize_revenue()
        self.assertEqual(self.project.revenue_recognized_to_date, 5000.0)

        # Raising the budget lowers percent_complete/recognized_revenue -- must reverse, not
        # post a raw negative line.
        self.project.total_budgeted_cost = 200.0
        self.project.invalidate_recordset()
        self.assertEqual(self.project.recognized_revenue, 2500.0)
        self.project.action_recognize_revenue()
        self.assertEqual(self.project.revenue_recognized_to_date, 2500.0)

        move = self.env["account.move"].search(
            [("journal_id", "=", self.env.ref("project_budget_recognition.journal_revenue_recognition").id)],
            limit=1, order="id desc",
        )
        wip_account = self.env.ref("project_budget_recognition.account_unbilled_receivable_wip")
        revenue_account = self.env.ref("project_budget_recognition.account_recognized_revenue")
        debit_line = move.line_ids.filtered(lambda l: l.account_id == revenue_account)
        credit_line = move.line_ids.filtered(lambda l: l.account_id == wip_account)
        self.assertEqual(debit_line.debit, 2500.0)
        self.assertEqual(credit_line.credit, 2500.0)

    def test_negative_total_budgeted_cost_blocked(self):
        with self.assertRaises(ValidationError):
            self.project.total_budgeted_cost = -50.0
            self.project.flush_recordset()

    def test_consumption_picking_project_locked_after_validation(self):
        other_project = self.env["project.project"].create({"name": "Other Project"})
        picking = self._consume(2.0, project=self.project)
        self.assertEqual(picking.state, "done")
        with self.assertRaises(ValidationError):
            picking.project_id = other_project.id
        with self.assertRaises(ValidationError):
            picking.project_id = False
