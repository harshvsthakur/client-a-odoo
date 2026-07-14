from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_is_zero


class ProjectProject(models.Model):
    _inherit = "project.project"

    committed_cost = fields.Monetary(
        string="Committed Cost",
        compute="_compute_committed_cost",
        currency_field="currency_id",
        help=(
            "Confirmed Purchase Order lines for service products, attributed to this "
            "project's analytic account. Deliberately excludes stockable goods -- those "
            "are counted in Consumption Cost instead, once, at the point of actual "
            "consumption, so the same cost isn't counted twice."
        ),
    )
    consumption_cost = fields.Monetary(
        string="Consumption Cost",
        compute="_compute_consumption_cost",
        currency_field="currency_id",
        help="Valuation of stock moved into Production Consumption, attributed to this project.",
    )
    cost_incurred = fields.Monetary(
        string="Cost Incurred",
        compute="_compute_cost_incurred",
        currency_field="currency_id",
    )
    total_budgeted_cost = fields.Monetary(
        string="Total Budgeted Cost",
        currency_field="currency_id",
        help="Manually estimated total cost for this project. Denominator for Percent Complete.",
    )
    percent_complete = fields.Float(
        string="Percent Complete",
        compute="_compute_percent_complete",
        digits=(5, 4),
        help="Cost Incurred / Total Budgeted Cost, capped at 100%. Stored as a 0-1 fraction (percentage widget).",
    )
    recognized_revenue = fields.Monetary(
        string="Recognized Revenue",
        compute="_compute_recognized_revenue",
        currency_field="currency_id",
        help="Percent Complete x the linked Sales Order's untaxed amount.",
    )
    revenue_recognized_to_date = fields.Monetary(
        string="Revenue Recognized to Date",
        currency_field="currency_id",
        readonly=True,
        copy=False,
        help="Cumulative amount already posted to the books via Recognize Revenue.",
    )

    @api.constrains("total_budgeted_cost")
    def _check_total_budgeted_cost_not_negative(self):
        for project in self:
            if project.total_budgeted_cost < 0:
                raise ValidationError(_("Total Budgeted Cost cannot be negative."))

    @api.model_create_multi
    def create(self, vals_list):
        projects = super().create(vals_list)
        plan = self.env.ref("analytic.analytic_plan_projects", raise_if_not_found=False)
        if plan:
            for project in projects:
                if not project.account_id:
                    project.account_id = self.env["account.analytic.account"].create({
                        "name": project.name,
                        "plan_id": plan.id,
                    })
        return projects

    def _committed_cost_domain(self):
        return [
            ("order_id.state", "=", "purchase"),
            ("product_id.product_tmpl_id.type", "=", "service"),
            ("distribution_analytic_account_ids", "in", self.account_id.ids),
        ]

    @api.depends("account_id")
    def _compute_committed_cost(self):
        for project in self:
            if not project.account_id:
                project.committed_cost = 0.0
                continue
            lines = self.env["purchase.order.line"].search(project._committed_cost_domain())
            account_key = str(project.account_id.id)
            total = 0.0
            for line in lines:
                for key, pct in (line.analytic_distribution or {}).items():
                    if account_key in key.split(","):
                        total += line.price_subtotal * (pct / 100.0)
            project.committed_cost = total

    @api.depends("account_id")
    def _compute_consumption_cost(self):
        consume_type = self.env.ref(
            "stock_store_production_route.picking_type_production_consume",
            raise_if_not_found=False,
        )
        for project in self:
            if not consume_type or not project.account_id:
                project.consumption_cost = 0.0
                continue
            layers = self.env["stock.valuation.layer"].search([
                ("stock_move_id.picking_id.project_id", "=", project.id),
                ("stock_move_id.picking_id.picking_type_id", "=", consume_type.id),
            ])
            project.consumption_cost = abs(sum(layers.mapped("value")))

    @api.depends("committed_cost", "consumption_cost")
    def _compute_cost_incurred(self):
        for project in self:
            project.cost_incurred = project.committed_cost + project.consumption_cost

    @api.depends("cost_incurred", "total_budgeted_cost")
    def _compute_percent_complete(self):
        for project in self:
            if float_is_zero(project.total_budgeted_cost, precision_digits=2):
                project.percent_complete = 0.0
            else:
                project.percent_complete = min(
                    project.cost_incurred / project.total_budgeted_cost, 1.0
                )

    @api.depends("percent_complete", "sale_order_id.amount_untaxed")
    def _compute_recognized_revenue(self):
        for project in self:
            project.recognized_revenue = (
                project.percent_complete * project.sale_order_id.amount_untaxed
            )

    def action_recognize_revenue(self):
        self.ensure_one()
        delta = self.recognized_revenue - self.revenue_recognized_to_date
        if float_is_zero(delta, precision_digits=2):
            raise UserError(_(
                "Nothing to recognize -- recognized revenue is unchanged since the last posting."
            ))

        journal = self.env.ref("project_budget_recognition.journal_revenue_recognition")
        wip_account = self.env.ref("project_budget_recognition.account_unbilled_receivable_wip")
        revenue_account = self.env.ref("project_budget_recognition.account_recognized_revenue")
        analytic_distribution = {str(self.account_id.id): 100.0} if self.account_id else False

        if delta > 0:
            debit_account, credit_account = wip_account, revenue_account
        else:
            # Downward revision: proper reversal, not a raw negative-amount line.
            debit_account, credit_account = revenue_account, wip_account
        amount = abs(delta)

        move = self.env["account.move"].create({
            "journal_id": journal.id,
            "date": fields.Date.context_today(self),
            "ref": _("Revenue recognition -- %s", self.name),
            "line_ids": [
                (0, 0, {
                    "name": self.name,
                    "account_id": debit_account.id,
                    "debit": amount,
                    "credit": 0.0,
                    "analytic_distribution": analytic_distribution,
                }),
                (0, 0, {
                    "name": self.name,
                    "account_id": credit_account.id,
                    "debit": 0.0,
                    "credit": amount,
                    "analytic_distribution": analytic_distribution,
                }),
            ],
        })
        move.action_post()
        self.revenue_recognized_to_date += delta
        return True
