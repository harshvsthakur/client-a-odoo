from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    contact_preference = fields.Selection(
        [
            ("email", "Email"),
            ("phone", "Phone"),
            ("sms", "SMS"),
            ("whatsapp", "WhatsApp"),
            ("mail", "Mail (Post)"),
        ],
        string="Contact Preference",
    )
