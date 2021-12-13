from odoo.addons.sale.tests.test_sale_order import TestSaleOrder
from odoo.tests import Form, tagged


@tagged('cluedoo')
class TestSaleOrderApproval(TestSaleOrder):
    def test_sale_order_approval(self):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        is_approval = ICPSudo.get_param('fal_config_setting.fal_is_proposal')

        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
        })
        self.sol_product_order = self.env['sale.order.line'].create({
            'name': self.company_data['product_order_no'].name,
            'product_id': self.company_data['product_order_no'].id,
            'product_uom_qty': 2,
            'product_uom': self.company_data['product_order_no'].uom_id.id,
            'price_unit': self.company_data['product_order_no'].list_price,
            'order_id': self.sale_order.id,
            'tax_id': False,
        })

        user = self.env.user
        # set user group to purchase user
        user.write({'groups_id': [(6, None, self.env.ref("sales_team.group_sale_salesman").ids)]})

        self.sale_order.with_user(user).action_propose()
        if is_approval:
            self.assertEqual(self.sale_order.state, 'waitingapproval')
        else:
            self.assertEqual(self.sale_order.state, 'sale')
