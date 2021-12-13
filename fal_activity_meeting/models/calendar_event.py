from odoo import models, fields, api, _
import datetime
from datetime import timedelta
from odoo.exceptions import ValidationError


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    @api.model
    def create(self, vals):
        calendar = super(CalendarEvent, self).create(vals)
        if self._context.get('event_id'):
            self.env['mail.activity'].browse(self._context.get('event_id')).meeting_id = calendar.id
        return calendar
