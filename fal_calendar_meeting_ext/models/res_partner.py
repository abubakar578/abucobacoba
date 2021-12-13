# -*- coding: utf-8 -*-
from odoo import fields, models


class res_partner(models.Model):
    _inherit = 'res.partner'

    fal_meeting_category = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')], 'Category', )
    fal_standard_rates = fields.Many2one(
        'fal.meeting.standard.rates', 'Standard Rates', )


class fal_meeting_standard_rates(models.Model):
    _name = "fal.meeting.standard.rates"
    _description = 'Meeting Standard Rates'

    name = fields.Char('Category Name')
    fal_partner_meeting_category = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')], 'Partner Meeting Category',)
    rates = fields.Monetary("Standard Rates")
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.user.company_id.currency_id)
