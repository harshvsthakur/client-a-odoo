{
    "name": "Project Templates",
    "version": "18.0.1.0.0",
    "summary": "User-defined project templates (task list + milestones) with mandatory template selection when creating a project from the UI",
    "category": "Project",
    "depends": ["project"],
    "data": [
        "security/ir.model.access.csv",
        "views/project_template_views.xml",
        "views/project_project_views.xml",
        "views/project_task_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
