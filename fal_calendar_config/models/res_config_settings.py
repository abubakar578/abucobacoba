# -*- coding: utf-8 -*-
from odoo import fields, models, api


class FalResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_fal_meeting_project = fields.Boolean(
        'Project to Meeting')

    module_fal_meeting_timesheet = fields.Boolean(
        'Meeting to Timesheet')

    module_fal_calendar_meeting_ext = fields.Boolean(
        'Meeting Management - Light version')
