from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    sales_admin_id = fields.Many2one('res.users', string='CSS')
    email_domain = fields.Char('Email Domain', readonly=False, store=True, compute='_email_domain')

    @api.depends('email', 'is_company')
    def _email_domain(self):
        for item in self:
            if item.is_company and item.email:
                domain = item.email.split('@')
                item.email_domain = domain[1]
                if '>' in domain[1]:
                    check_domain = domain[1].split('>')
                    item.email_domain = check_domain[0]
            else:
                item.email_domain = False
