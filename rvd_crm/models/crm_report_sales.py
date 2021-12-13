# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime, timedelta

import logging

_logger = logging.getLogger(__name__)


class CrmReportSales(models.Model):
    _name = 'crm.report.sales'

    sales_admin_id = fields.Many2one('res.users', string='CSS',default=lambda self: self.env.user)
    sales_person_id = fields.Many2one('res.users', string='Sales Person', default=lambda self: self.env.user)
    is_sales_admin = fields.Boolean("Is CSS")
    is_sales_person = fields.Boolean("Is Sales Person")
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    percentage = fields.Float('Percentage', compute='_total_percantage')
    total = fields.Float('Total', compute='_compute_total')
    record_crm_ids = fields.Many2many('record.crm', string='Record CRM', readonly=True, store=True)
    record_activity_ids = fields.Many2many(
        'record.activity', string='Reporting List', compute='_default_reporting_list')

    def name_get(self):
        res = super(CrmReportSales, self).name_get()
        for report_sale in self:
            name = 'Report: '
            if self.is_sales_admin:
                name = name + report_sale.sales_admin_id.name
            elif self.sales_person_id:
                name = name + report_sale.sales_person_id.name
            res.append((report_sale.id, name))
        return res

    @api.depends('record_crm_ids')
    def _default_reporting_list(self):
        for item in self:
            temp = []
            if item.record_crm_ids and item.is_sales_person:
                # group by update date
                groups = item.record_crm_ids.read_group([('sales_person_id', '=', self.sales_person_id.id)], ['new_date', 'new_stage'], ['new_date:day'])
                total_act = 0
                total_p2q = 0
                total_p2w = 0
                total_lost = 0
                total_won = 0
                for group in groups:
                    date_group = datetime.strptime(group.get('new_date:day'), '%d %b %Y').date()
                    # check record and fill to record activity
                    for record_crm in item.record_crm_ids.filtered(lambda x: x.new_date.date() == date_group and x.new_stage):
                        if record_crm.old_stage == self.env.ref('crm.stage_lead3') and record_crm.new_stage == self.env.ref('crm.stage_lead2'):
                            total_p2q += 1
                        elif record_crm.old_stage == self.env.ref('crm.stage_lead3') and record_crm.new_stage == self.env.ref('crm.stage_lead4'):
                            total_p2w += 1
                        elif record_crm.new_stage == self.env.ref('rvd_crm.stage_lost'):
                            total_lost += 1
                        elif record_crm.new_stage == self.env.ref('crm.stage_lead4'):
                            total_won += 1
                        elif record_crm.crm_lead_id.message_ids.filtered(lambda z: z.subtype_id.name == "Discussions" and z.body):
                            total_act += 1
                    temp.append((0, 0, {
                        'date': date_group,
                        'total_activity': total_act,
                        'total_p2q': total_p2q,
                        'total_p2w': total_p2w,
                        'total_lost': total_lost,
                        'total_won': total_won,
                        'sales_person_id': self.sales_person_id.id,
                    }))
            item.record_activity_ids = temp

    @api.depends('total', 'record_crm_ids')
    def _total_percantage(self):
        for item in self:
            total_percentage = 0.0
            if item.record_crm_ids:
                if item.is_sales_admin:
                    total_crm = len(item.record_crm_ids)
                    total_percentage += item.total / total_crm
            item.percentage = total_percentage

    @api.depends('record_crm_ids')
    def _compute_total(self):
        for item in self:
            total_minutes = 0.0
            if item.is_sales_admin:
                for stg in item.record_crm_ids:
                    total_minutes += stg.duration
            item.total = total_minutes

    # fill record crm
    @api.onchange('start_date', 'end_date', 'sales_admin_id', 'sales_person_id')
    def _onchange_tracking_stage(self):
        for item in self:
            if item.is_sales_admin:
                stage_quoted = self.env.ref('crm.stage_lead2')
                stage_responded = self.env.ref('crm.stage_lead3')
                track_stage_ids = self.env['record.crm'].search([
                    ('create_date_crm', '>=', self.start_date),
                    ('create_date_crm', '<=', self.end_date),
                    ('sales_admin_id', '=', self.sales_admin_id.id),
                    ('old_stage', '=', stage_responded.id),
                    ('new_stage', '=', stage_quoted.id),
                ]).filtered(lambda x: x.new_stage)
                item.record_crm_ids = [(6, 0, track_stage_ids.ids)]
            elif item.is_sales_person:
                track_stage_ids = self.env['record.crm'].search([
                    ('create_date_crm', '>=', self.start_date),
                    ('create_date_crm', '<=', self.end_date),
                    ('sales_person_id', '=', self.sales_person_id.id),
                ]).filtered(lambda x: x.new_stage)
                item.record_crm_ids = [(6, 0, track_stage_ids.ids)]
