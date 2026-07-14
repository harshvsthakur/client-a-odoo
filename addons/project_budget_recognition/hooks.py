def post_init_hook(env):
    """Backfill an analytic account onto every existing project that doesn't have one yet --
    committed_cost/consumption_cost can't attribute anything to a project without it."""
    plan = env.ref("analytic.analytic_plan_projects", raise_if_not_found=False)
    if not plan:
        return
    projects = env["project.project"].search([("account_id", "=", False)])
    for project in projects:
        project.account_id = env["account.analytic.account"].create({
            "name": project.name,
            "plan_id": plan.id,
        })
