from odoo import api, fields, models, _
from odoo.osv import expression
import logging

_logger = logging.getLogger(__name__)


class ProductBrand(models.Model):
    _inherit = "product.brand"


    active = fields.Boolean('Active', default=True)

    def action_merge_brand(self):
        context = self.env.context

        view = self.env.ref('rvd_product_code.view_merge_brand_form')
        return {
            'name': _('List Brand'),
            'res_model': 'merge.brand',
            'view_mode': 'form',
            'context': {
                'active_model': 'product.brand',
                'active_ids': context.get('active_ids'),
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
