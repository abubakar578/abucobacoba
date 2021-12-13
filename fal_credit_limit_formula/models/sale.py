# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _

from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_propose(self):
        for so in self:
            if self.user_has_groups('sales_team.group_sale_manager'):
                return super(SaleOrder, self).action_propose()
            else:
                res = so.validate_so_credit_limit()
                if res:
                    return res
                else:
                    return super(SaleOrder, self).action_propose()
        return super(SaleOrder, self).action_propose()

    def validate_so_credit_limit(self):
        # check if no customer is set, or customer is not to validate
        if not self.partner_id or self.partner_id.fal_sale_warning_type != 'percentage':
            return False

        so_uninvoice_amount = self.sudo().get_so_uninvoiced_amount()
        account_receivable = self.partner_id.credit

        # AR + Uninvoice Amount + current SO total amount
        computed_credit = (account_receivable + so_uninvoice_amount + self.amount_total)

        # when the restrict credit limit is reached, Block.
        if ((1 + (self.partner_id.fal_limit_restrict_margin / 100)) * (self.partner_id.credit_limit)) < computed_credit:
            raise UserError(_("Can not propose order due to restricted customer credit limit."))
        # If the remaining credit limit is less than warning margin give a warning.
        elif ((1 - (self.partner_id.fal_limit_warning_margin / 100)) * (self.partner_id.credit_limit)) <= computed_credit:
            remaining_credit = (self.partner_id.credit_limit - computed_credit)
            # showing Warning pop up if remaining credit less than warning margin
            context = dict(self._context or {})
            if context.get('sale_force_confirm'):
                return False

            alert_wizard_obj = self.env['fal.alert.wizard']
            if remaining_credit >= 0:
                msg = (_("If you Confirm this Quotation, remaining credit will be almost over (%s) left. Confirm to continue or cancel.") % (remaining_credit))
            else:
                msg = (_("If you Confirm this Quotation, credit limit will be exceeded by (%s). Confirm to continue or cancel.") % (remaining_credit))
            wizard_id = alert_wizard_obj.create({
                'sale_order_id': self.id,
                'message': msg
            })
            # showing wizard form view
            view = self.env.ref('fal_credit_limit_formula.view_fal_alert_wizard')
            return {
                'name': _('Sales Confirmation'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'fal.alert.wizard',
                'views': [(view.id, 'form')],
                'view_id': view.id,
                'target': 'new',
                'res_id': wizard_id.id
            }
        return False

    def get_so_uninvoiced_amount(self):
        sale_order_line_obj = self.env['sale.order.line']
        so_paid_amount = 0
        # Find All UnInvoiced SO Line
        so_line_uninvoice_ids = sale_order_line_obj.search([('order_partner_id', '=', self.partner_id.id), ('state', 'in', ['sale', 'done']), ('untaxed_amount_to_invoice', '>', 0)])
        for data in so_line_uninvoice_ids:
            if data.currency_id != self.partner_id.currency_id:
                so_paid_amount_converted = data.currency_id._convert(
                    data.untaxed_amount_to_invoice,
                    self.partner_id.currency_id,
                    data.company_id,
                    data.order_id.date_order or fields.Date.today()
                )
                so_paid_amount += so_paid_amount_converted
            else:
                so_paid_amount += data.untaxed_amount_to_invoice
        return so_paid_amount
