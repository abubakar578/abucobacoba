from odoo import fields, models, tools, api


class ActivityReport(models.Model):
    """ CRM Lead Analysis """
    _inherit = "crm.activity.report"

    tracking_message = fields.Html('Tracking Message', readonly=True)
    sales_admin_id = fields.Many2one('res.users', string='CSS', tracking=True)

    def _select(self):
        res = super(ActivityReport, self)._select()
        res += ', m.tracking_message, l.sales_admin_id'
        return res

    def _where(self):
        disccusion_subtype = self.env.ref('mail.mt_comment')
        return """
            WHERE
                m.model = 'crm.lead' AND (m.mail_activity_type_id IS NOT NULL OR m.subtype_id = %s OR m.tracking_count > 0)
        """ % (disccusion_subtype.id,)
