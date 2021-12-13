from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class RitmaShippingCost(models.Model):
    _name = 'ritma.shipping.cost'
    _description = "Ritma Shipping Cost"


    name = fields.Char("Name")
    delivery_by = fields.Selection(
        [('udara', 'Udara'),
         ('darat', 'Darat'),
         ('laut', 'Laut'),
        ], string="Delivery By", default='darat')
    uom_delivery = fields.Selection(
        [('kg', 'Kg'),
         ('volume', 'Volumes'),
        ], string="Uom", default='kg')
    price_unit = fields.Float("Price")
    minimum_qty = fields.Float("Min. Qty")
    from_wh = fields.Many2one('stock.location', string="From", domain="[('usage', '=', 'internal')]")
    destination_wh = fields.Many2one('stock.location', string="Destination", domain="[('usage', '=', 'internal')]")
    transit = fields.Boolean('Transit')


class RouteWarehouse(models.Model):
    _name = 'route.warehouse'

    order_line_id = fields.Many2one('sale.order.line', string="Line")
    from_wh_id = fields.Many2one('stock.location', string="From Warehouse")
    quantity = fields.Integer(string="Quantity")
    price_unit = fields.Float(string="Price")
    product_id = fields.Many2one('product.product', string="Product")
    location_id = fields.Many2one(related='order_line_id.warehouse_id.lot_stock_id')
    total_weight = fields.Float(string="Weight")
    total_volume = fields.Float(string="volume")
    delivery_by = fields.Many2one('ritma.shipping.cost', string="By")

    def _compute_price(self, route_wh, qty):
        price = 0
        if route_wh.uom_delivery == 'kg':
            res_result = self.total_weight * qty
            if res_result > route_wh.minimum_qty:
                res_price = res_result * route_wh.price_unit
                price = res_price
            else:
                price = route_wh.minimum_qty * route_wh.price_unit
        if route_wh.uom_delivery == 'volume':
            res_result = self.total_volume * qty
            if res_result > route_wh.minimum_qty:
                res_price = res_result * route_wh.price_unit
                price = res_price
            else:
                price = route_wh.minimum_qty * route_wh.price_unit

        return price

    @api.onchange('quantity', 'delivery_by')
    def onchange_price_unit(self):
        if self.delivery_by:
            self.order_line_id.done_add_ship = False
            self.price_unit = self._compute_price(self.delivery_by, self.quantity)

    @api.onchange('from_wh_id')
    def onchange_from_location(self):
        if self.from_wh_id:
            domain = [
                ('from_wh', '=', self.from_wh_id.id),
                ('destination_wh', '=', self.order_line_id.warehouse_id.lot_stock_id.id),
            ]
            return {'domain': {'delivery_by': domain}}
