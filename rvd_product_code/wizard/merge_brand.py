from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class MergeBrands(models.TransientModel):
    _name = 'merge.brand'

    def _get_list_brands(self):
        context = self.env.context
        active_ids = context.get('active_ids')
        brands = self.env['product.brand'].search([('id', 'in', active_ids)])
        return brands

    product_brand_id = fields.Many2one('product.brand', 'Brand Merge to', domain="[('id', 'in', list_brand_ids)]")
    list_brand_ids = fields.Many2many('product.brand', string='Brand List', default=_get_list_brands)

    def merge_brand(self):
        for brand in self.env.context.get('active_ids'):
            if brand != self.product_brand_id.id:
                products_archive = self.env['product.template'].search([('active', '=', False), ('product_brand_id', '=', brand)])
                products = self.env['product.template'].search([('product_brand_id', '=', brand)])
                if products_archive:
                    for product in products_archive:
                        product.write({'product_brand_id': self.product_brand_id.id})
                elif products:
                    for product in products:
                        product.write({'product_brand_id': self.product_brand_id.id})

                brand = self.env['product.brand'].browse(brand)
                brand.unlink()
        return
