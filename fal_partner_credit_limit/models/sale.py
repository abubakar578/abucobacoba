# -*- coding:utf-8 -*-
from odoo import models, fields
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as df


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_proposal(self):
        if super(SaleOrder, self)._check_proposal():
            return True
        else:
            if self.partner_id.fal_sale_warning_type == 'blocked':
                return True
            elif self.partner_id.fal_sale_warning_type == 'value':
                if self.amount_total > self.partner_id.fal_remaining_credit_limit:
                    return True
            elif self.partner_id.fal_sale_warning_type == 'days':
                if self._check_overdue_invoice():
                    return True
            elif self.partner_id.fal_sale_warning_type == 'valuedate':
                if self.amount_total > self.partner_id.fal_remaining_credit_limit:
                    return True
                if self._check_overdue_invoice():
                    return True
                # This means partner are checked but both test are good
                return False
            else:
                return False

    def _check_overdue_invoice(self):
        blck_lvl = self.partner_id.fal_block_level
        current_position = self.partner_id.fal_deptor_position
        if blck_lvl:
            if blck_lvl > current_position:
                return False
            else:
                return True
