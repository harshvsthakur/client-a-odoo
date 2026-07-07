from datetime import timedelta

from odoo import api, fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    template_id = fields.Many2one(
        "project.template",
        string="Project Template",
        help=(
            "Template this project was created from. Seeds the project's "
            "initial task list and milestones on creation. Required in the "
            "UI when creating a project (not at the database level, so "
            "automatic project creation such as sale_project's Sales Order "
            "confirmation flow is unaffected)."
        ),
    )

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        for project, vals in zip(projects, vals_list):
            if vals.get("template_id"):
                project._apply_template()
        return projects

    def _apply_template(self):
        self.ensure_one()
        template = self.template_id
        if not template:
            return
        start = self.date_start or fields.Date.context_today(self)

        if template.task_line_ids:
            self.env["project.task"].create(
                [
                    {
                        "project_id": self.id,
                        "name": line.name,
                        "planned_date_start": start + timedelta(days=line.start_offset),
                        "planned_date_end": start + timedelta(days=line.end_offset),
                    }
                    for line in template.task_line_ids
                ]
            )

        if template.milestone_line_ids:
            self.allow_milestones = True
            self.env["project.milestone"].create(
                [
                    {
                        "project_id": self.id,
                        "name": line.name,
                        "deadline": start + timedelta(days=line.deadline_offset),
                    }
                    for line in template.milestone_line_ids
                ]
            )
