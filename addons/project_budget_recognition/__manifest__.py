{
    "name": "Project Budget Recognition",
    "version": "18.0.1.0.0",
    "summary": "Percentage-of-completion revenue recognition per project, driven by committed PO costs and production consumptions.",
    "category": "Project",
    "depends": ["project", "purchase", "stock_account", "stock_store_production_route", "sale_project"],
    "data": [
        "data/account_data.xml",
        "views/project_project_views.xml",
        "views/stock_picking_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
