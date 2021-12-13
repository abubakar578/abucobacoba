from odoo import api, fields, models, _


class crm_lead_workflow_wizard(models.TransientModel):
    _name = 'fal.alert.wizard'
    _description = 'Falinwa Alert Wizard'

    message = fields.Char(string='Message', readonly=True)
    sale_order_id = fields.Many2one("sale.order", string="Sale Order")

    def action_sale_propose(self):
        context = dict(self._context or {})
        context.update({'sale_force_confirm': True})
        self.sale_order_id.with_context(context).action_wait()
