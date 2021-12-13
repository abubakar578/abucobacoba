# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class ResultProduct(models.TransientModel):
    _inherit = 'result.product'

    lead_id = fields.Many2one('crm.lead', 'Lead')
    is_lead = fields.Boolean(string='Lead')

    def create_enquiry(self):
        order_lines = []
        context = self.env.context
        order_id = context.get('order')
        for wizard_line in self.mapped('rvd_stock_product_ids').filtered(lambda x: x.prod_ok):
            if self.is_lead:
                enquiry = self.env['customer.enquiry.line'].create({
                    'rvd_sku': wizard_line.product_tmpl_id.name,
                    'lead_id': context.get('lead_id'),
                    'quantity': wizard_line.reserve,
                })
                _logger.info(enquiry)
        return enquiry


class RvdProductSku(models.TransientModel):
    _inherit = "rvd.product.sku"

    lead_id = fields.Many2one('crm.lead', 'Lead')
