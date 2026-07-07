from odoo import fields, models


class ProjectTemplate(models.Model):
    _name = "project.template"
    _description = "Project Template"

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    task_line_ids = fields.One2many(
        "project.template.task", "template_id", string="Task List"
    )
    milestone_line_ids = fields.One2many(
        "project.template.milestone", "template_id", string="Milestones"
    )


class ProjectTemplateTask(models.Model):
    _name = "project.template.task"
    _description = "Project Template Task Line"
    _order = "sequence, id"

    template_id = fields.Many2one(
        "project.template", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, string="Task Title")
    start_offset = fields.Integer(
        string="Planned Start (days after project start)",
        default=0,
        help="Days after the project's start date this task is planned to begin.",
    )
    end_offset = fields.Integer(
        string="Planned End (days after project start)",
        default=0,
        help="Days after the project's start date this task is planned to end.",
    )


class ProjectTemplateMilestone(models.Model):
    _name = "project.template.milestone"
    _description = "Project Template Milestone Line"
    _order = "sequence, id"

    template_id = fields.Many2one(
        "project.template", required=True, ondelete="cascade"
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(required=True)
    deadline_offset = fields.Integer(
        string="Deadline (days after project start)",
        default=0,
        help="Days after the project's start date this milestone is due.",
    )
