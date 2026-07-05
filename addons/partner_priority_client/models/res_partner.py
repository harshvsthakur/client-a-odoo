from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_priority_client = fields.Boolean(string="Priority Client")
    priority_level = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
        ],
        string="Priority Level",
        required=True,
        default="medium",
    )
