{
    "name": "Project Type Field",
    "version": "18.0.1.0.0",
    "summary": "Adds a Project Type (Permanent / SPAA) classification field to Projects",
    "category": "Project",
    "depends": ["project"],
    "data": [
        "views/project_project_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
