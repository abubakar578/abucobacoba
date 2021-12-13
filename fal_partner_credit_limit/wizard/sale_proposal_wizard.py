
# -*- coding: utf-8 -*-
from odoo import models, api, fields


class sale_propose_wizard(models.TransientModel):
    _inherit = "fal.sale.proposal.wizard"

    is_blocked = fields.Boolean("is_blocked", compute="_check_restriction")
    is_over_credit = fields.Boolean(
        "is_over_credit", compute="_check_restriction")
    unpaid_invoice = fields.Boolean(
        "unpaid invoices", compute="_check_restriction")

    @api.depends('sale_order_id')
    def _check_restriction(self):
        for order_line in self.sale_order_id:
            if order_line.partner_id.fal_sale_warning_type == 'blocked':
                self.is_blocked = True
            elif order_line.partner_id.fal_sale_warning_type == 'value':
                if order_line.amount_total > order_line.partner_id.fal_remaining_credit_limit:
                    self.is_over_credit = True
                else:
                    self.is_over_credit = False
            elif order_line.partner_id.fal_sale_warning_type == 'days':
                if order_line._check_overdue_invoice():
                    self.unpaid_invoice = True
                else:
                    self.unpaid_invoice = False
            elif order_line.partner_id.fal_sale_warning_type == 'valuedate':
                if order_line.amount_total > order_line.partner_id.fal_remaining_credit_limit:
                    self.is_over_credit = True
                else:
                    self.is_over_credit = False
                if order_line._check_overdue_invoice():
                    self.unpaid_invoice = True
                else:
                    self.unpaid_invoice = False
            else:
                self.is_blocked = False
