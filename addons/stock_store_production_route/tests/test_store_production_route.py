from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase


class TestStoreProductionRoute(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.categ = cls.env.ref(
            "stock_store_production_route.product_category_production_materials"
        )
        cls.store = cls.env.ref("stock_store_production_route.stock_location_store")
        cls.production = cls.env.ref(
            "stock_store_production_route.stock_location_production_floor"
        )
        cls.consumption = cls.env.ref(
            "stock_store_production_route.stock_location_production_consumption"
        )
        cls.pt_store_to_production = cls.env.ref(
            "stock_store_production_route.picking_type_store_to_production"
        )
        cls.pt_consume = cls.env.ref(
            "stock_store_production_route.picking_type_production_consume"
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Raw Material",
                "type": "consu",
                "is_storable": True,
                "categ_id": cls.categ.id,
                "standard_price": 10.0,
            }
        )
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.store, 100.0)

    def _validate(self, picking):
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.picked = True
        picking.button_validate()

    def test_category_uses_avco_and_automated_valuation(self):
        self.assertEqual(self.categ.property_cost_method, "average")
        self.assertEqual(self.categ.property_valuation, "real_time")

    def test_pick_and_store_moves_stock_from_store_to_production(self):
        Quant = self.env["stock.quant"]
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.pt_store_to_production.id,
                "location_id": self.store.id,
                "location_dest_id": self.production.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 10.0,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.store.id,
                            "location_dest_id": self.production.id,
                        },
                    )
                ],
            }
        )
        self._validate(picking)
        self.assertEqual(picking.state, "done")
        self.assertEqual(Quant._get_available_quantity(self.product, self.store), 90.0)
        self.assertEqual(Quant._get_available_quantity(self.product, self.production), 10.0)

    def test_consume_posts_avco_cogs_journal_entry(self):
        Quant = self.env["stock.quant"]
        Quant._update_available_quantity(self.product, self.production, 10.0)

        consume = self.env["stock.picking"].create(
            {
                "picking_type_id": self.pt_consume.id,
                "location_id": self.production.id,
                "location_dest_id": self.consumption.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 4.0,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.production.id,
                            "location_dest_id": self.consumption.id,
                        },
                    )
                ],
            }
        )
        self._validate(consume)
        self.assertEqual(consume.state, "done")

        valuation_layers = consume.move_ids.stock_valuation_layer_ids
        self.assertEqual(len(valuation_layers), 1)
        self.assertEqual(valuation_layers.quantity, -4.0)
        self.assertEqual(valuation_layers.value, -40.0)  # 4 units * standard_price 10.0, AVCO

        account_move = valuation_layers.account_move_id
        self.assertTrue(account_move, "Consume move should post an accounting entry")
        self.assertEqual(account_move.state, "posted")

    def test_return_wizard_reverses_store_to_production(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.pt_store_to_production.id,
                "location_id": self.store.id,
                "location_dest_id": self.production.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 10.0,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.store.id,
                            "location_dest_id": self.production.id,
                        },
                    )
                ],
            }
        )
        self._validate(picking)

        return_wizard = (
            self.env["stock.return.picking"]
            .with_context(active_id=picking.id, active_model="stock.picking")
            .create({})
        )
        for line in return_wizard.product_return_moves:
            line.quantity = 10.0
        result = return_wizard.action_create_returns()
        return_picking = self.env["stock.picking"].browse(result["res_id"])

        self.assertEqual(return_picking.location_id, self.production)
        self.assertEqual(return_picking.location_dest_id, self.store)

    def test_insufficient_store_stock_prompts_backorder_not_silent_failure(self):
        # Only 100 units in Store (setUpClass); request 500. Odoo reserves what's
        # available and, on validate, prompts for a backorder rather than erroring
        # or silently moving the full requested quantity. Documenting this as
        # expected core behavior, not a gap this module needs to close.
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.pt_store_to_production.id,
                "location_id": self.store.id,
                "location_dest_id": self.production.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 500.0,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.store.id,
                            "location_dest_id": self.production.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.picked = True
        result = picking.button_validate()
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("res_model"), "stock.backorder.confirmation")
        self.assertEqual(picking.state, "assigned")  # not yet done, awaiting the wizard

    def test_zero_quantity_move_blocked_at_validate(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.pt_store_to_production.id,
                "location_id": self.store.id,
                "location_dest_id": self.production.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": 0.0,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.store.id,
                            "location_dest_id": self.production.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        with self.assertRaises(UserError):
            picking.button_validate()

    def test_negative_quantity_move_is_neutralized_at_confirm(self):
        # Core Odoo doesn't reject a negative product_uom_qty at create(), but
        # action_confirm() reduces the move's demand to 0 rather than moving
        # stock backwards -- verifying that guarantee holds for our operation type.
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.pt_store_to_production.id,
                "location_id": self.store.id,
                "location_dest_id": self.production.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "product_id": self.product.id,
                            "product_uom_qty": -3.0,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.store.id,
                            "location_dest_id": self.production.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        self.assertEqual(picking.move_ids.product_uom_qty, 0.0)
        with self.assertRaises(UserError):
            picking.button_validate()

    def test_stock_user_can_operate_the_new_picking_type(self):
        stock_user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "TCK8 Stock Tester",
                "login": "tck8_stock_tester",
                "groups_id": [
                    (
                        6,
                        0,
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("stock.group_stock_user").id,
                        ],
                    )
                ],
            }
        )
        picking = (
            self.env["stock.picking"]
            .with_user(stock_user)
            .create(
                {
                    "picking_type_id": self.pt_store_to_production.id,
                    "location_id": self.store.id,
                    "location_dest_id": self.production.id,
                    "move_ids": [
                        (
                            0,
                            0,
                            {
                                "name": self.product.name,
                                "product_id": self.product.id,
                                "product_uom_qty": 1.0,
                                "product_uom": self.product.uom_id.id,
                                "location_id": self.store.id,
                                "location_dest_id": self.production.id,
                            },
                        )
                    ],
                }
            )
        )
        picking.with_user(stock_user).action_confirm()
        # With full stock available, confirm auto-reserves straight to "assigned".
        self.assertEqual(picking.state, "assigned")

    def test_user_without_stock_group_cannot_create_transfer(self):
        plain_user = self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "TCK8 Plain Tester",
                "login": "tck8_plain_tester",
                "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
            }
        )
        with self.assertRaises(AccessError):
            self.env["stock.picking"].with_user(plain_user).create(
                {
                    "picking_type_id": self.pt_store_to_production.id,
                    "location_id": self.store.id,
                    "location_dest_id": self.production.id,
                    "move_ids": [
                        (
                            0,
                            0,
                            {
                                "name": self.product.name,
                                "product_id": self.product.id,
                                "product_uom_qty": 1.0,
                                "product_uom": self.product.uom_id.id,
                                "location_id": self.store.id,
                                "location_dest_id": self.production.id,
                            },
                        )
                    ],
                }
            )
