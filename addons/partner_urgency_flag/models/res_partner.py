from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_urgent = fields.Boolean(string="Urgent Follow-up")
