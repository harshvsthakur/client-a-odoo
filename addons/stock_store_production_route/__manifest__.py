{
    "name": "Store / Production Route",
    "version": "18.0.1.0.0",
    "summary": "Store and Production locations, a manual internal-transfer route between them, and a consumption route out of Production, with AVCO/automated valuation.",
    "depends": ["stock", "stock_account"],
    "data": [
        "data/stock_locations.xml",
        "data/product_category.xml",
        "data/stock_picking_types.xml",
    ],
    "installable": True,
    "application": False,
}
