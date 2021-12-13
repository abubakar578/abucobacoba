from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProductNonStock(models.TransientModel):
    _name = 'product.non.stock'

    sku_name = fields.Char("SKU Name")
    enquiry_id = fields.Many2one('customer.enquiry.line', string="Enquiry")
    non_stock_line_ids = fields.Many2many('product.non.stock.line', 'line_id', 'stock_line_rel', string="Route Warehouse", readonly=False)

    def _prepare_so_line(self, order, line, price):
        price_unit = price
        if order.pricelist_id:
            items = order.pricelist_id._compute_price_rule_get_items([(line.product_id, line.quantity, order.partner_id)], fields.Date.today(), line.quantity, line.product_id.product_tmpl_id.ids, line.product_id.ids, line.product_id.categ_id.ids)
            if items:
                if items[0]:
                    compute_price = items[0].landed_cost + items[0].price_discount / 100
                    price_unit =  price + compute_price

        return {
            'name': line.product_char,
            'order_id': order.id,
            'product_id': line.product_id.id,
            'product_uom_qty': line.quantity,
            'price_unit': price_unit,
            'harga_non_stock': price_unit,
        }

    def create_so_line(self):
        order_line = self.env['sale.order.line']
        context = self._context
        price = 0.0
        order = self.env['sale.order'].browse(context.get('order_id'))
        # get price
        for line in self.non_stock_line_ids:
            if line.price > price:
                price = 0
                price += line.price

        for line in self.non_stock_line_ids:
            if not line.product_id:
                raise UserError("Please create product")
            line_vals = self._prepare_so_line(order, line, price)
            order_line.create(line_vals)
        return

    
class ProductNonStockLine(models.TransientModel):
    _name = 'product.non.stock.line'

    quantity = fields.Integer("Quantity")
    price = fields.Float("Price")
    product_char = fields.Char("Product Name")
    product_id = fields.Many2one('product.product', string="Product", domain="['|', ('name', 'like', product_char), ('processed_name', '=', product_char)]")
    vendor_id = fields.Many2one('res.partner', "Vendor")
    uom_id = fields.Many2one('uom.uom', "Unit of Measure")

    @api.onchange('product_id', 'vendor_id')
    def onchange_product_uom(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            if self.vendor_id:
                seller = self.product_id._select_seller(
                    partner_id=self.vendor_id,
                    uom_id=self.uom_id,
                    quantity=self.quantity)
                if seller:
                    self.price = seller.price
