from odoo import api, fields, models, registry, SUPERUSER_ID, _
import logging

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'


    delivery_type = fields.Selection(selection_add=[
        ('internal_ship', 'Internal Ship'),],
            ondelete={'internal_ship': lambda recs: recs.write({'delivery_type': 'fixed', 'fixed_price': 0,
        })})
    delivery_by = fields.Selection(
        [('udara', 'Udara'),
         ('darat', 'Darat'),
        ], string="Delivery By", default='darat')
    uom_delivery = fields.Selection(
        [('kg', 'Kg'),
         ('volume', 'Volumes'),
        ], string="Uom", default='kg')
    price_unit = fields.Float("Price")
    minimum_qty = fields.Float("Min. Qty")
    from_wh = fields.Many2one('stock.warehouse', string="From")
    destination_wh = fields.Many2one('stock.warehouse', string="Destination")

    # override
    def rate_shipment(self, order):
        self.ensure_one()
        if hasattr(self, '%s_rate_shipment' % self.delivery_type):
            res = getattr(self, '%s_rate_shipment' % self.delivery_type)(order)
            # apply margin on computed price
            res['price'] = float(res['price']) * (1.0 + (self.margin / 100.0))
            # save the real price in case a free_over rule overide it to 0
            res['carrier_price'] = res['price']
            # free when order is large enough
            if res['success'] and self.free_over and order._compute_amount_total_without_delivery() >= self.amount:
                res['warning_message'] = _('The shipping is free since the order amount exceeds %.2f.') % (self.amount)
                res['price'] = 0.0
        # getattr tidak dapat balikan, jadi dibuat kondisi jika melakukan internal ship
        if self.delivery_type == 'internal_ship':
            res = {'success': True, 'price': 0.0, 'error_message': False, 'warning_message': False}
            res['success'] = True
            res['price'] = self.price_unit
            res['carrier_price'] = res['price']
            
        return res
