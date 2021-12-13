from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.constrains('ref', 'product_brand_id')
    def _check_unique_ref(self):
        for product in self:
            product_find = self.with_context(active_test=False).search([('name', '=', product.name), ('product_brand_id', '=', product.product_brand_id.id)])
            _logger.info(product_find)
            if len(product_find) >= 2:
                raise UserError(_('Product : "%s", with Brand : "%s" already exist. Must be unique.' % (product.name, product.product_brand_id.name)))

    cross_reference_ids = fields.Many2many('product.template', 'x_product_template_cross_rel', 'cross_id', 'product_tmpl_id', context={'active_test': False}, string='Cross Reference', readonly=False, tracking=True)
    rvd_product_attributes_ids = fields.One2many('rvd.product.attribute', 'product_tmpl_id', string='Attributes', readonly=False, tracking=True)
    product_equipment_ids = fields.One2many('product.equipment', 'product_tmpl_id', string='Product Equipment', readonly=False, tracking=True)


class RvdProductAttributes(models.Model):
    _name = 'rvd.product.attribute'

    def _get_value_flt(self):
        for att in self:
            value = att.value
            # att.value_int = float(value)
            try:
                att.value_int = float(value)
            except Exception as e:
                _logger.info('=======%r', e)
                att.value_int = 0.0
    #         #     counter = 0
    #         #     for c in value:
    #         #         counter+=1

    #         #     # if counter < 1000:
    #         #     # else:
    #         #     #     pass
    #         #     pass

    name = fields.Char(string='Key', required=True)
    value = fields.Char(string='Value')
    value_int = fields.Float(string='Value Int', compute='_get_value_flt', store=True)
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')


class ProductEquipment(models.Model):
    _name = 'product.equipment'

    name = fields.Char(string="Equipment", required=True)
    year = fields.Char(string="Year")
    equipment_type = fields.Char(string="Equipment Type")
    equipment_options = fields.Char(string="Equipment Options")
    engine = fields.Char(string="Engine")
    engine_options = fields.Char(string="Engine Options")
    fuel = fields.Char(string="Fuel")
    cc = fields.Char(string="CC")
    kw = fields.Char(string="kW")
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')

    # def unlink(self):
    #     if self.product_tmpl_id:
    #         raise UserError(_("Can't Delete This Equipment(Crawling)"))
    #     return super().unlink()


class ProductBrand(models.Model):
    _inherit = "product.brand"

    priority = fields.Integer(string="Priority", default=99)
