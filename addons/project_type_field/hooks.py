def post_init_hook(env):
    env.cr.execute(
        "UPDATE project_project SET project_type = %s WHERE project_type IS NULL",
        ("permanent",),
    )
