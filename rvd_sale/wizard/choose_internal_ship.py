from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ChooseProductSelect(models.Model):
    _name = 'choose.product.select'

    so_line_id = fields.Many2one('sale.order.line', 'Order Line')
    so_line_ids = fields.Many2many('sale.order.line', 'choose_product_rel','sale_order_line_rel', string="So Line")
    choose_line_ids = fields.Many2many('choose.product.select.line', 'chooose_id', string="Choose Product", readonly=False)

    def applied_customer_select(self):
        for line in self.choose_line_ids.filtered(lambda o: not o.is_select):
            for so_line in self.so_line_ids.filtered(lambda l: l.product_id == line.product_id):
                so_line.flush()
                so_line.unlink()
        return


class ChooseProductSelectLine(models.TransientModel):
    _name = 'choose.product.select.line'

    choose_product_id = fields.Many2one('choose.product.select', 'Choose')
    product_tmpl_id = fields.Many2one('product.template', 'Product Template')
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Quantity')
    price = fields.Float('Price')
    name = fields.Char('Price')
    is_select = fields.Boolean(string='Select')


class ChooseInternShip(models.TransientModel):
    _name = 'choose.internal.shipping'

    def get_compute_route_warehouse(self):
        for int_ship in self:
            context = self._context
            for res_id in context.get('routes'):
                route_wh = self.env['route.warehouse'].browse(res_id)
                int_ship.route_warehouse_ids = route_wh

    route_warehouse_ids = fields.Many2many('route.warehouse', string="Route Warehouse", compute='get_compute_route_warehouse', readonly=False)
