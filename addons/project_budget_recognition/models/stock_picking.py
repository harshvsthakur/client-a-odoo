from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    project_id = fields.Many2one(
        "project.project",
        string="Project",
        help="Which project this consumption is attributed to, for budget recognition.",
    )

    @api.constrains("project_id", "picking_type_id", "state")
    def _check_project_required_for_consumption(self):
        consume_type = self.env.ref(
            "stock_store_production_route.picking_type_production_consume",
            raise_if_not_found=False,
        )
        if not consume_type:
            return
        for picking in self:
            if (
                picking.state == "done"
                and picking.picking_type_id == consume_type
                and not picking.project_id
            ):
                raise ValidationError(
                    _("A Production Consume transfer must be linked to a Project before it can be validated.")
                )

    def write(self, vals):
        if "project_id" in vals:
            for picking in self:
                if picking.state == "done" and picking.project_id.id != vals["project_id"]:
                    raise ValidationError(_(
                        "This transfer is already validated and its cost has been attributed "
                        "to %s -- the Project can no longer be changed.",
                        picking.project_id.name,
                    ))
        return super().write(vals)
