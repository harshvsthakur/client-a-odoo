from odoo import _, models
from odoo.exceptions import UserError


class ProjectProject(models.Model):
    _inherit = "project.project"

    def action_view_sale_order_ux(self):
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_("This project has no related Sales Order."))
        return {
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self.sale_order_id.id,
            "view_mode": "form",
            "target": "current",
        }
