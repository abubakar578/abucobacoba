from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from odoo.exceptions import RedirectWarning, UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _check_proposal(self):

        if self.user_has_groups('sales_team.group_sale_manager'):
            return False
        else:
            ICPSudo = self.env['ir.config_parameter'].sudo()
            if ICPSudo.get_param('fal_config_setting.fal_is_proposal'):
                return True
            else:
                return False

    def action_propose(self):
        if self._check_proposal():
            if self.user_has_groups('sales_team.group_sale_manager'):
                self.action_confirm()
            else:
                self.action_wait()

        else:
            self.action_confirm()

    state = fields.Selection(selection_add=[
        ('waitingapproval', 'Wait Approval'),
    ])

    def action_wait(self):
        orders = self.filtered(lambda s: s.state in ['draft', 'sent'])
        return orders.write({
            'state': 'waitingapproval',
        })
        