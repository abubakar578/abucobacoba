# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ResultProduct(models.TransientModel):
    _name = 'result.product'

    def _get_products(self):
        prod_id = self.env.context.get('product_list')
        product = self.env['product.template'].browse(prod_id)
        return product

    def _check_request(self):
        for wiz in self:
            qty = self.env.context.get('limit_quantity')
            wiz.request_qty = qty

    @api.onchange("rvd_sku", "brand_id", "rvd_attribute_ids", "rvd_equipment_ids")
    def onchange_product(self):
        order_id = self.env.context.get('order')
        # sku and brand
        if self.rvd_sku and not self.rvd_equipment_ids and not self.rvd_attribute_ids:
            prod_ref = self.env['product.template'].search([('processed_name', '=', self.rvd_sku), ('active', '=', True)], limit=1)
            prod_ref_archive = self.env['product.template'].search([('processed_name', '=', self.rvd_sku), ('active', '=', False)], limit=1)
            if prod_ref or prod_ref_archive:
                ritma_codes = self.env['rvd.product.code'].search([
                    ('cross_reference_ids', 'in', prod_ref.id or prod_ref_archive.id)
                ])
            if ritma_codes:
                temp = []
                list_prod = []
                for prod_sku in self.rvd_product_sku_ids:
                    list_prod.append(prod_sku.ritma_code_id.id)

                for code in ritma_codes:
                    if code.id not in list_prod:
                        for product in code.product_tmpl_ids:
                            temp.append({
                                'product_tmpl_id': product.id,
                                'product_variant_id': product.product_variant_id.id,
                                'ritma_code_id': product.rvd_product_template_code_id.id,
                                'brand_id': product.product_brand_id.id,
                                'price': product.list_price,
                                'description': product.description,
                                'order_id': order_id,
                            })
                    rvd_product = self.env['rvd.product.sku'].create(temp)
                self.rvd_product_sku_ids += rvd_product
        # equipment
        if self.rvd_equipment_ids:
            _logger.info("Equipment")
            ritma_codes = self.env['rvd.product.code'].search([
                ('product_equipment_ids', 'in', self.rvd_equipment_ids.ids),
            ])
            if ritma_codes:
                temp = []
                list_prod = []
                for prod_sku in self.rvd_product_sku_ids:
                    list_prod.append(prod_sku.ritma_code_id.id)

    #             for code in ritma_codes:
    #                 if code.id not in list_prod:
    #                     for product in code.product_tmpl_ids:
    #                         temp.append({
    #                             'product_tmpl_id': product.id,
    #                             'product_variant_id': product.product_variant_id.id,
    #                             'ritma_code_id': product.rvd_product_template_code_id.id,
    #                             'brand_id': product.product_brand_id.id,
    #                             'price': product.list_price,
    #                             'description': product.description,
    #                             'order_id': order_id,
    #                         })
    #                 rvd_product = self.env['rvd.product.sku'].create(temp)
    #             self.rvd_product_sku_ids += rvd_product
    #     # attribute
        # if self.rvd_attribute_ids:
        #     ritma_codes = self.env['rvd.product.code'].search([
        #         ('rvd_product_attributes_ids', 'in', self.rvd_attribute_ids.ids),
        #     ])
        #     if ritma_codes:
        #         temp = []
        #         list_prod = []
        #         for prod_sku in self.rvd_product_sku_ids:
        #             list_prod.append(prod_sku.ritma_code_id.id)

        #         for code in ritma_codes:
        #             if code.id not in list_prod:
        #                 for product in code.product_tmpl_ids:
        #                     temp.append({
        #                         'product_tmpl_id': product.id,
        #                         'product_variant_id': product.product_variant_id.id,
        #                         'ritma_code_id': product.rvd_product_template_code_id.id,
        #                         'brand_id': product.product_brand_id.id,
        #                         'price': product.list_price,
        #                         'description': product.description,
        #                         'order_id': order_id,
        #                     })
        #             rvd_product = self.env['rvd.product.sku'].create(temp)
        #         self.rvd_product_sku_ids += rvd_product

    @api.onchange("rvd_product_sku_ids.select_prod", "rvd_product_sku_ids")
    def onchange_warehouse(self):
        # select data product
        order_id = self.env.context.get('order')
        order = self.env['sale.order'].browse(order_id)
        limit_qty = self.env.context.get('limit_quantity')
        self.rvd_stock_product_ids = False
        rvd_product = False
        for product_sku in self.rvd_product_sku_ids:
            res_sku = self.env['rvd.product.sku'].browse(product_sku)
            result = []
            gap_qty = limit_qty
            if product_sku.select_prod:
                list_wh = []
                # use WH rule internal in partner
                # if order.partner_id.rule_wh_id.rules_line_ids:
                #     for line in order.partner_id.rule_wh_id.rules_line_ids:
                #         list_wh.append(line.warehouse_id.id)
                #         # check stock on WH

                #         warehouse = line.warehouse_id
                #         onhand = product_sku.product_tmpl_id.with_context(warehouse=warehouse.id).qty_available
                #         virtual_qty = product_sku.product_tmpl_id.with_context(warehouse=warehouse.id).virtual_available
                #         incoming_qty = product_sku.product_tmpl_id.with_context(warehouse=warehouse.id).incoming_qty
                #         outgoing_qty = product_sku.product_tmpl_id.with_context(warehouse=warehouse.id).outgoing_qty
                #         stock_quant = self.env['stock.quant'].search([('product_id', '=', product_sku.product_variant_id.id), ('location_id', '=', warehouse.lot_stock_id.id)])
                #         # add to stock
                #         if gap_qty and gap_qty > onhand:
                #             result.append(self._prepare_values_check_stock(warehouse, onhand, order, product_sku, incoming_qty, outgoing_qty, virtual_qty, stock_quant, onhand))
                #             gap_qty = limit_qty - onhand

                #         else:
                #             result.append(self._prepare_values_check_stock(warehouse, onhand, order, product_sku, incoming_qty, outgoing_qty, virtual_qty, stock_quant, gap_qty))
                #             gap_qty = 0

                #     rvd_product = self.env['rvd.stock.product'].create(result)

                # warehouse not in rule internal partner
                for warehouse in self.env['stock.warehouse'].search([]):
                    if warehouse.id not in list_wh:
                        onhand = product_sku.product_tmpl_id.with_context(warehouse=warehouse.id).qty_available
                        virtual_qty = product_sku.product_tmpl_id.with_context(warehouse=warehouse.id).virtual_available
                        incoming_qty = product_sku.product_tmpl_id.with_context(warehouse=warehouse.id).incoming_qty
                        outgoing_qty = product_sku.product_tmpl_id.with_context(warehouse=warehouse.id).outgoing_qty
                        stock_quant = self.env['stock.quant'].search([('product_id', '=', product_sku.product_variant_id.id), ('location_id', '=', warehouse.lot_stock_id.id)])
                        # add to stock
                        result.append(self._prepare_values_check_stock(warehouse, onhand, order, product_sku, incoming_qty, outgoing_qty, virtual_qty, stock_quant, gap_qty))
                        gap_qty = 0
                
                    rvd_product = self.env['rvd.stock.product'].create(result)
                self.rvd_stock_product_ids |= rvd_product

    def _prepare_values_check_stock(self, warehouse, onhand, order, product, incoming, outgoing, virtual_qty, quant, reserve=False):
        return {
            'rvd_stock_location_id': warehouse.lot_stock_id.id,
            'warehouse_id': warehouse.id,
            'rvd_on_hand': onhand,
            'order_id': order.id,
            'rvd_product_sku_id': product.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'ritma_code_id': product.product_tmpl_id.rvd_product_template_code_id.id,
            'product_variant_id': product.product_variant_id.id,
            'stock_quant_ids': [(6, 0, quant.ids)],
            'outgoing_qty': outgoing,
            'incoming_qty': incoming,
            'virtual_qty': virtual_qty,
            'reserve': reserve or 0.0,
        }

    def _prepare_choose_product_line(self, product):
        return {
            'product_id': product.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'name': product.name,
        }

    def choose_product(self):
        cp_line_obj = self.env['choose.product.select.line']
        cp_id = False
        cp_list = []
        for wizard_line in self.mapped('rvd_product_sku_ids').filtered(lambda x: x.reserve > 0):
            values_line = self._prepare_choose_product_line(wizard_line.product_variant_id)
            cp_lind_id = cp_line_obj.create(values_line)
            cp_list.append(cp_lind_id.id)
            cp_id = self.env['choose.product.select'].create({
                'choose_line_ids': [(6, 0, cp_list)]
            })
        return cp_id

    def _check_order_id(self, context=False):
        order_id = context.get('order') or context.get('active_id')
        order = self.env['sale.order'].browse(order_id) or False
        return order


    def create_order_line_percepatan(self):
        context = self.env.context
        order_line = self.env['sale.order.line']
        order = self._check_order_id(context)
        if order:
            so_list = []
            cp_list = []
            choose_method = self.choose_product()
            section = order_line.create({
                'display_type': 'line_section',
                'name': self.section_name,
                'order_id': order.id,
                'choose_product_id': choose_method.id,
            })
            for wizard_line in self.mapped('rvd_product_sku_ids').filtered(lambda x: x.reserve > 0):
                if wizard_line.reserve != self.request_qty:
                    raise ValidationError(_("Quantity must be same with Request"))
                else:
                    res = wizard_line.with_context({'active_id': wizard_line.id}).fal_create_so_line_direct(order, self.request_qty, True, self.section_name)
                    so_list.append(res.id)
            section.choose_product_id.write({
                'so_line_ids' : [(6, 0, so_list)]
            })
        return

    def create_order_line_direct(self):
        context = self.env.context
        order_line = self.env['sale.order.line']
        cp_line_obj = self.env['choose.product.select.line']
        order = self._check_order_id(context)
        if order:
            so_list = []
            cp_list = []
            choose_method = self.choose_product()
            _logger.info("XXXXXXXXXXX")
            _logger.info(self.section_name)
            section = order_line.create({
                'display_type': 'line_section',
                'name': self.section_name,
                'order_id': order.id,
                'choose_product_id': choose_method.id,
            })
            _logger.info("XXXXXXXXXXX")
            for wizard_line in self.mapped('rvd_product_sku_ids').filtered(lambda x: x.reserve > 0):
                if wizard_line.reserve != self.request_qty:
                    raise ValidationError(_("Quantity must be same with Request"))
                else:
                    res = wizard_line.with_context({'active_id': wizard_line.id}).fal_create_so_line_direct(order, self.request_qty, False, self.section_name)
                    so_list.append(res.id)
            section.choose_product_id.write({
                'so_line_ids' : [(6, 0, so_list)]
            })
        return

    section_name = fields.Char("Section Name")
    product_tmpl_ids = fields.Many2many('product.template', 'result_product_rel', string="Product", default=_get_products)
    brand_id = fields.Many2one('product.brand', 'Brand')
    is_attribute = fields.Boolean(string='Attribute')
    request_qty = fields.Integer("Request Qty", compute='_check_request')

    rvd_sku = fields.Char('SKU')
    rvd_stock_product_ids = fields.One2many('rvd.stock.product', 'result_product_id', string='Stock')
    rvd_product_sku_ids = fields.One2many('rvd.product.sku', 'result_product_id', string="Product")
    rvd_attribute_ids = fields.Many2many('rvd.product.attribute', string='Attribute')
    rvd_equipment_ids = fields.Many2many('product.equipment', string='Equipment')
    ritma_code_ids = fields.Many2many('rvd.product.code', string='Ritma Code')


class RvdStockProduct(models.TransientModel):
    _name = "rvd.stock.product"

    rvd_stock_location_id = fields.Many2one('stock.location', string="Location")
    rvd_product_sku_id = fields.Many2one('rvd.product.sku', string="SKU Selection")
    prod_ok = fields.Boolean(string='Ok')
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    rvd_on_hand = fields.Float(string="On Hand")
    outgoing_qty = fields.Float(string="Outgoing Qty")
    incoming_qty = fields.Float(string="Incoming Qty")
    virtual_qty = fields.Float(string="Virtual Qty")
    reserve = fields.Integer(string="Reserve")
    stock_quant_ids = fields.Many2many('stock.quant', string="Stock Quant")
    product_tmpl_id = fields.Many2one('product.template', string="Product Template")
    product_variant_id = fields.Many2one('product.product', related='product_tmpl_id.product_variant_id', string="Product")
    result_product_id = fields.Many2one('result.product', string="Product Variant")
    order_id = fields.Many2one('sale.order', 'Order')
    ritma_code_id = fields.Many2one('rvd.product.code', string='Ritma Code')


    def _prepare_order_line_vals(self, order_id):
        values = {
            'name': self.ritma_code_id.description or self.product_tmpl_id.name,
            'rvd_merk': self.product_tmpl_id.product_brand_id.name,
            'product_template_id': self.product_tmpl_id.id,
            'product_id': self.product_variant_id.id,
            'price_unit': order_id.pricelist_id.get_product_price(self.product_variant_id, self.reserve, order_id.partner_id, uom_id=self.product_tmpl_id.uom_id.id),
            'harga_satuan': order_id.pricelist_id.get_product_price(self.product_variant_id, self.reserve, order_id.partner_id, uom_id=self.product_tmpl_id.uom_id.id),
            'product_uom_qty': self.reserve,
            'from_wh_id': self.warehouse_id.id,
            'order_id': order_id.id,
        }
        return values


    def fal_create_so_line(self, order_id):
        order_line = self.env['sale.order.line']
        values_line = self._prepare_order_line_vals(order_id)
        line = order_line.create(values_line)
        return


class RvdProductSku(models.TransientModel):
    _name = "rvd.product.sku"

    product_tmpl_id = fields.Many2one('product.template', string="Product Template")
    product_variant_id = fields.Many2one('product.product', related='product_tmpl_id.product_variant_id', string="Product")
    brand_id = fields.Many2one('product.brand', string="Brand")
    result_product_id = fields.Many2one('result.product', string="Product Variant")
    price = fields.Float(string="Sales Price")
    select_prod = fields.Boolean(string="Sales Price")
    description = fields.Char(string="Description")
    order_id = fields.Many2one('sale.order', 'Order')
    ritma_code_id = fields.Many2one('rvd.product.code', string='Ritma Code')
    desc_stock = fields.Char("Stock Information")
    reserve = fields.Integer(string="Reserve")
    height = fields.Float(string='Height 1')
    height2 = fields.Float(string='Height 2')
    od1 = fields.Float(string='OD 1')
    od2 = fields.Float(string='OD 2')
    id1 = fields.Float(string='ID 1')
    id2 = fields.Float(string='ID 2')
    flange_hat = fields.Float(string='Flange Hat')
    length = fields.Float(string='Length 1')
    length2 = fields.Float(string='Length 2')
    width = fields.Float(string='Width 1')
    width2 = fields.Float(string='Width 2')
    thread = fields.Float(string='Thread')
    litre = fields.Float(string='Litre')
    ampere = fields.Float(string='Ampere')
    is_attribute = fields.Boolean(string='attribute')

    def _prepare_direct_order_line_vals(self, order_id, request_qty):
        _logger.info("XXXXXXXXXXX")
        values = {
            'name': self.description or self.product_tmpl_id.name,
            'product_template_id': self.product_tmpl_id.id,
            'product_id': self.product_variant_id.id,
            'price_unit': order_id.pricelist_id.get_product_price(self.product_variant_id, request_qty, order_id.partner_id, uom_id=self.product_tmpl_id.uom_id.id),
            'harga_satuan': order_id.pricelist_id.get_product_price(self.product_variant_id, request_qty, order_id.partner_id, uom_id=self.product_tmpl_id.uom_id.id),
            'product_uom_qty': self.reserve,
            'from_wh_id': self.order_id.warehouse_id.id,
            'rvd_merk': self.brand_id.name,
            'order_id': order_id.id,
        }
        return values


    def fal_create_so_line_direct(self, order_id, request_qty, percepatan=False, section_name=False):
        order_line = self.env['sale.order.line']
        values_line = self._prepare_direct_order_line_vals(order_id, request_qty)
        if percepatan:
            route = self.env['stock.location.route'].search([('percepatan_select', '=', True), ('sale_selectable', '=', True), ('warehouse_ids', '=', order_id.warehouse_id.id)], limit=1)
            values_line.update({
                'route_id': route.id
            })
        line = order_line.create(values_line)
        return line
