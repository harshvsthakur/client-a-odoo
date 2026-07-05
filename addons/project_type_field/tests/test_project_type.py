from odoo.tests.common import TransactionCase

from ..hooks import post_init_hook


class TestProjectType(TransactionCase):
    def test_blank_by_default_and_optional_at_orm_level(self):
        # project_type is required in the form view only, not at the
        # model/DB level -- sale_project's automatic project creation on
        # Sales Order confirmation, and project_sale_order_ux's own tests,
        # create projects without setting it and must keep working.
        project = self.env["project.project"].create({"name": "No Type Project"})
        self.assertFalse(project.project_type)

    def test_explicit_values_accepted(self):
        for value in ("permanent", "spaa"):
            project = self.env["project.project"].create(
                {"name": f"{value} project", "project_type": value}
            )
            self.assertEqual(project.project_type, value)

    def test_invalid_value_rejected(self):
        with self.assertRaises(ValueError):
            self.env["project.project"].create(
                {"name": "Bad Type Project", "project_type": "urgent"}
            )

    def test_post_init_hook_backfills_existing_blank_projects(self):
        project = self.env["project.project"].create({"name": "Legacy Project"})
        self.assertFalse(project.project_type)
        post_init_hook(self.env)
        project.invalidate_recordset(["project_type"])
        self.assertEqual(project.project_type, "permanent")

    def test_post_init_hook_does_not_override_existing_value(self):
        project = self.env["project.project"].create(
            {"name": "Already SPAA Project", "project_type": "spaa"}
        )
        post_init_hook(self.env)
        project.invalidate_recordset(["project_type"])
        self.assertEqual(project.project_type, "spaa")
