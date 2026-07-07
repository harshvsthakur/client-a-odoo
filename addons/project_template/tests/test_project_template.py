from datetime import date, timedelta

from psycopg2.errors import NotNullViolation

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


class TestProjectTemplate(TransactionCase):
    def _create_template(self, with_tasks=True, with_milestones=True):
        vals = {"name": "Standard Implementation"}
        template = self.env["project.template"].create(vals)
        if with_tasks:
            self.env["project.template.task"].create(
                [
                    {
                        "template_id": template.id,
                        "name": "Kickoff",
                        "start_offset": 0,
                        "end_offset": 1,
                    },
                    {
                        "template_id": template.id,
                        "name": "Go live",
                        "start_offset": 30,
                        "end_offset": 35,
                    },
                ]
            )
        if with_milestones:
            self.env["project.template.milestone"].create(
                {
                    "template_id": template.id,
                    "name": "Contract signed",
                    "deadline_offset": 7,
                }
            )
        return template

    def test_blank_by_default_and_optional_at_orm_level(self):
        # template_id is required in the form view only, not at the
        # model/DB level -- sale_project's automatic project creation on
        # Sales Order confirmation must keep working without a template.
        project = self.env["project.project"].create({"name": "No Template Project"})
        self.assertFalse(project.template_id)
        self.assertFalse(project.task_ids)

    def test_creating_project_with_template_instantiates_tasks_and_milestones(self):
        template = self._create_template()
        start = date(2026, 1, 1)
        project = self.env["project.project"].create(
            {
                "name": "Templated Project",
                "template_id": template.id,
                "date_start": start,
            }
        )
        self.assertEqual(len(project.task_ids), 2)
        kickoff = project.task_ids.filtered(lambda t: t.name == "Kickoff")
        self.assertEqual(kickoff.planned_date_start, start)
        self.assertEqual(kickoff.planned_date_end, start + timedelta(days=1))
        go_live = project.task_ids.filtered(lambda t: t.name == "Go live")
        self.assertEqual(go_live.planned_date_start, start + timedelta(days=30))
        self.assertEqual(go_live.planned_date_end, start + timedelta(days=35))

        self.assertTrue(project.allow_milestones)
        self.assertEqual(len(project.milestone_ids), 1)
        self.assertEqual(project.milestone_ids.deadline, start + timedelta(days=7))

    def test_template_without_start_date_falls_back_to_today(self):
        template = self._create_template(with_milestones=False)
        project = self.env["project.project"].create(
            {"name": "No Start Date Project", "template_id": template.id}
        )
        today = date.today()
        kickoff = project.task_ids.filtered(lambda t: t.name == "Kickoff")
        self.assertEqual(kickoff.planned_date_start, today)

    def test_template_with_no_lines_creates_no_tasks_or_milestones(self):
        template = self._create_template(with_tasks=False, with_milestones=False)
        project = self.env["project.project"].create(
            {"name": "Empty Template Project", "template_id": template.id}
        )
        self.assertFalse(project.task_ids)
        self.assertFalse(project.milestone_ids)
        self.assertFalse(project.allow_milestones)

    def test_reusing_same_template_for_multiple_projects(self):
        template = self._create_template()
        project_a = self.env["project.project"].create(
            {"name": "Project A", "template_id": template.id}
        )
        project_b = self.env["project.project"].create(
            {"name": "Project B", "template_id": template.id}
        )
        self.assertEqual(len(project_a.task_ids), 2)
        self.assertEqual(len(project_b.task_ids), 2)
        self.assertNotEqual(project_a.task_ids.ids, project_b.task_ids.ids)

    # -- Edge cases --------------------------------------------------

    def test_blank_task_or_milestone_name_rejected(self):
        template = self.env["project.template"].create({"name": "Edge Cases"})
        with mute_logger("odoo.sql_db"), self.assertRaises(NotNullViolation):
            self.env["project.template.task"].create(
                {"template_id": template.id, "name": False}
            )

    def test_special_characters_in_names_round_trip_unchanged(self):
        tricky_name = "Kick-off <script>alert('x')</script> — \"quoted\" 日本語 & more"
        template = self.env["project.template"].create({"name": tricky_name})
        task = self.env["project.template.task"].create(
            {"template_id": template.id, "name": tricky_name}
        )
        project = self.env["project.project"].create(
            {"name": "Special Char Project", "template_id": template.id}
        )
        self.assertEqual(template.name, tricky_name)
        self.assertEqual(task.name, tricky_name)
        self.assertEqual(project.task_ids.name, tricky_name)

    def test_negative_offset_treated_as_before_project_start(self):
        # No constraint forbids a negative offset -- e.g. "prep work due 3
        # days before the project starts" is a legitimate use case.
        template = self._create_template(with_milestones=False)
        self.env["project.template.task"].create(
            {
                "template_id": template.id,
                "name": "Pre-kickoff prep",
                "start_offset": -3,
                "end_offset": -1,
            }
        )
        start = date(2026, 1, 10)
        project = self.env["project.project"].create(
            {"name": "Negative Offset Project", "template_id": template.id, "date_start": start}
        )
        prep = project.task_ids.filtered(lambda t: t.name == "Pre-kickoff prep")
        self.assertEqual(prep.planned_date_start, start - timedelta(days=3))
        self.assertEqual(prep.planned_date_end, start - timedelta(days=1))

    def test_very_large_offset_does_not_error(self):
        template = self.env["project.template"].create({"name": "Far Future"})
        self.env["project.template.milestone"].create(
            {
                "template_id": template.id,
                "name": "Long-term milestone",
                "deadline_offset": 36500,  # ~100 years
            }
        )
        project = self.env["project.project"].create(
            {
                "name": "Far Future Project",
                "template_id": template.id,
                "date_start": date(2026, 1, 1),
            }
        )
        self.assertEqual(project.milestone_ids.deadline, date(2026, 1, 1) + timedelta(days=36500))

    def test_task_or_milestone_line_requires_a_template(self):
        with mute_logger("odoo.sql_db"), self.assertRaises(NotNullViolation):
            self.env["project.template.task"].create({"name": "Orphan task"})

    def test_deleting_template_nulls_out_reference_on_existing_projects(self):
        # template_id has no explicit ondelete, so Odoo defaults it to
        # 'set null' -- deleting a template must not delete or block
        # deletion of projects that were created from it.
        template = self._create_template(with_milestones=False)
        project = self.env["project.project"].create(
            {"name": "Orphaned Template Project", "template_id": template.id}
        )
        template.unlink()
        self.assertFalse(project.exists() and project.template_id)
        self.assertTrue(project.exists())
        # Tasks already instantiated from the template are untouched.
        self.assertEqual(len(project.task_ids), 2)

    def test_non_manager_cannot_create_or_edit_templates(self):
        user = self.env["res.users"].create(
            {
                "name": "Regular Project User",
                "login": "project_user_no_manager",
                "email": "project_user_no_manager@example.com",
                "groups_id": [(6, 0, [self.env.ref("project.group_project_user").id])],
            }
        )
        template = self._create_template()
        with self.assertRaises(AccessError):
            self.env["project.template"].with_user(user).create({"name": "Not allowed"})
        with self.assertRaises(AccessError):
            template.with_user(user).write({"name": "Also not allowed"})
        # Read access (needed to pick a template on a project) is fine.
        self.assertTrue(template.with_user(user).name)

    def test_project_creator_needs_no_extra_rights_beyond_manager_to_use_a_template(self):
        # Core Odoo already restricts project.project create/write/unlink to
        # group_project_manager -- group_project_user is read-only there.
        # Confirm picking a template doesn't require any additional grant:
        # a manager can create a templated project without needing
        # separate write/create access on project.template itself.
        user = self.env["res.users"].create(
            {
                "name": "Project Manager",
                "login": "project_manager_no_extra_rights",
                "email": "project_manager_no_extra_rights@example.com",
                "groups_id": [(6, 0, [self.env.ref("project.group_project_manager").id])],
            }
        )
        template = self._create_template()
        project = self.env["project.project"].with_user(user).create(
            {"name": "Created By Manager", "template_id": template.id}
        )
        self.assertEqual(len(project.task_ids), 2)

    def test_plain_project_user_cannot_create_any_project_template_or_not(self):
        # Pre-existing core Odoo behavior, not introduced by this module --
        # documented here so it's not mistaken for a bug in template_id's
        # access rights.
        user = self.env["res.users"].create(
            {
                "name": "Regular Project User",
                "login": "project_user_cannot_create_project",
                "email": "project_user_cannot_create_project@example.com",
                "groups_id": [(6, 0, [self.env.ref("project.group_project_user").id])],
            }
        )
        with self.assertRaises(AccessError):
            self.env["project.project"].with_user(user).create({"name": "Should Fail"})
