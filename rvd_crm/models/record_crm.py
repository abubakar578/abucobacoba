from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class RecordCrm(models.Model):
    _name = "record.crm"

    crm_lead_id = fields.Many2one('crm.lead', string="Crm Lead")
    sales_admin_id = fields.Many2one('res.users', string='CSS', related='crm_lead_id.sales_admin_id')
    sales_person_id = fields.Many2one('res.users', string='Sales Person', related='crm_lead_id.user_id')
    create_date_crm = fields.Datetime('New Date', related='crm_lead_id.create_date')
    new_date = fields.Datetime('New Date')
    old_date = fields.Datetime('Old Date')
    new_stage = fields.Many2one('crm.stage', 'New Stage', readonly=True)
    old_stage = fields.Many2one('crm.stage', 'Old Stage', readonly=True)
    duration = fields.Float('Duration', compute='_compute_difference')

    @api.depends('new_date', 'old_date')
    def _compute_difference(self):
        for gap in self:
            if gap.new_date and gap.old_date:
                duration = gap.new_date - gap.old_date
                result = duration.total_seconds() / 60
                gap.duration = result
            else:
                gap.duration = 0


class RecordActivity(models.Model):
    _name = "record.activity"

    total_activity = fields.Integer(string='Total Activity')
    total_p2q = fields.Integer(string='Responded to Quoted')
    total_p2w = fields.Integer(string='Responded to Won')
    total_lost = fields.Integer(string='Lost')
    total_won = fields.Integer(string='Won')
    date = fields.Date('Date')
    record_crm_id = fields.Many2one('record.crm', string="Record Crm")
    report_sales_id = fields.Many2one('crm.report.sales', string="Report Sales")
    sales_person_id = fields.Many2one('res.users', string="Sales Person")
