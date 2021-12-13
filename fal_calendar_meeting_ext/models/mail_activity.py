# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    @api.model
    def create(self, values):
        new_meeting = self._context.get('default_res_model')
        if new_meeting == 'calendar.event':
            values['calendar_event_id'] = self._context['default_res_id']
       
        return super(MailActivity, self).create(values)
