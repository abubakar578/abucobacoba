from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleGroupApproval(models.Model):
    _name = 'sale.group.approval'

    def _get_team_member(self):
        group_sale_manager = self.env.ref('sales_team.group_sale_manager')
        _logger.info(group_sale_manager)
        return [(6, 0, group_sale_manager.users.ids)]

    name = fields.Char("Name Percentage", compute="_compute_name")
    min_percent = fields.Float("Min Percentage")
    max_percent = fields.Float("Max Percentage")
    percentage = fields.Float("Percentage")
    manager_member_ids = fields.Many2many('res.users', 'manager_rel', 'approval_id', string='Manager Members', check_company=True, domain=[('share', '=', False)], default=_get_team_member)
    member_ids = fields.Many2many('res.users', 'approved_rel', 'approval_id', string='Members', domain="[('id', 'in', manager_member_ids)]")

    @api.depends('min_percent', 'max_percent')
    def _compute_name(self):
        for rec in self:
            rec.name = str(rec.min_percent)+ '%' + ' To ' + str(rec.max_percent) + '%'
