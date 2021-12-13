# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    fal_sale_warning_type = fields.Selection(selection_add=[('percentage', 'Percentage')], ondelete={'percentage': 'cascade'})
    fal_limit_restrict_margin = fields.Float(string='Restrict Margin (%)', default=10.0,
        help="Restrict transaction on credit limit reach margin. Block happened if: Credit Limit + (1 + % Margin)% < (Total AR + This SO Amount + Uninvoiced SO). Example Limit(10%) 1000 + 100 < (300 + 900 + 0), Blocked. First Checked")
    fal_limit_warning_margin = fields.Float(string="Warning Margin (%)", default=20.0,
        help="Give warning on credit limit on warning margin. Warning / Proposal Stage happened if: Credit Limit + (1 - % Margin)% <= (Total AR + This SO Amount + Uninvoiced SO). Example Warning(20%) 1000 - 200 < (300 + 600 + 0), Warning. Second Checked")
