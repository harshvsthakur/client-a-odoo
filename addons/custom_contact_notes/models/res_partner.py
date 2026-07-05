from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    vip_notes = fields.Text(string='VIP Notes')
