from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    project_type = fields.Selection(
        [
            ("permanent", "Permanent"),
            ("spaa", "SPAA"),
        ],
        string="Project Type",
        help="SPAA: Pop-Up project.",
    )
