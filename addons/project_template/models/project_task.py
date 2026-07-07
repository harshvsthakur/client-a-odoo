from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    planned_date_start = fields.Date(
        string="Planned Start",
        help="Planned start date, typically seeded from a project template's task list.",
    )
    planned_date_end = fields.Date(
        string="Planned End",
        help="Planned end date, typically seeded from a project template's task list.",
    )
