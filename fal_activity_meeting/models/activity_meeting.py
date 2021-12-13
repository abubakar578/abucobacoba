from odoo import models, fields, api, _
import datetime
from datetime import timedelta
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    _inherit = "mail.activity"

    meeting_subject = fields.Char(string='Meeting Subject')
    start_date = fields.Date(string='Start Date', default=fields.Date.today)
    stop_date = fields.Date(string='Stop Date', default=fields.Date.today)
    duration = fields.Float('Duration')
    start = fields.Datetime(string='Start', default=fields.Datetime.today, help="Start date of an event, without time for full days events")
    stop = fields.Datetime(string='Stop', default=fields.Datetime.today, compute='_compute_stop', help="Stop date of an event, without time for full days events")
    allday = fields.Boolean(string='All Day')
    meeting_id = fields.Many2one("calendar.event")

    def action_create_calendar_event(self):
        self.ensure_one()
        action = super(MailActivity, self).action_create_calendar_event()
        if self.start_date:
            action['context']['default_start_date'] = self.start_date
        if self.stop_date:
            action['context']['default_stop_date'] = self.stop_date
        if self.duration:
            action['context']['default_duration'] = self.duration
        if self.start:
            action['context']['default_start'] = self.start
        if self.stop:
            action['context']['default_stop'] = self.stop
        action['context']['default_allday'] = self.allday
        action['context']['event_id'] = self.id
        return action

    def action_close_dialog(self):
        res = super(MailActivity, self).action_close_dialog()
        if self.activity_type_id.name == 'Meeting':
            if self.calendar_event_id:
                data = {
                    'name': self.meeting_subject,
                    'allday': self.allday,
                    'start': self.start,
                    'stop': self.stop,
                    'duration': self.duration,

                }
                if self.allday:
                    data.update({
                        'start_date': self.start_date,
                        'stop_date': self.stop_date,
                        'duration': self.duration,
                    })
                self.calendar_event_id.write(data)
        return res

    @api.onchange('meeting_subject')
    def _onchange_meeting_subjet(self):
        if self.meeting_subject:
            self.summary = self.meeting_subject

    @api.onchange('start_date')
    def _onchange_start_date(self):
        if self.start_date:
            self.start = datetime.datetime.combine(self.start_date, datetime.time.min)

    @api.onchange('stop_date')
    def _onchange_stop_date(self):
        if self.stop_date:
            self.stop = datetime.datetime.combine(self.stop_date, datetime.time.max)

    @api.constrains('start_date', 'stop_date')
    def _check_closing_date(self):
        for meeting in self:
            if meeting.start_date and meeting.stop_date and meeting.stop_date < meeting.start_date:
                raise ValidationError(
                    _('The ending date cannot be earlier than the starting date.') + '\n' +
                    _("Meeting '%s' starts '%s' and ends '%s'") % (meeting.meeting_subject, meeting.start_date, meeting.stop_date)
                )

    def create_meeting(self):
        meeting_obj = self.env['calendar.event']
        values = {
            'name': self.meeting_subject,
            'allday': self.allday,
            'start': self.start,
            'stop': self.stop,
            'duration': self.duration,
            'activity_ids': [(6, 0, self.ids)],
        }
        if self.allday:
            values.update({
                'start_date': self.start_date,
                'stop_date': self.stop_date,
            })
        meeting_id = meeting_obj.create(values)
        self.meeting_id = meeting_id

    @api.model
    def get_meeeting_id(self, ids):
        act_id = int(''.join([n for n in ids['activity_id'] if n.isdigit()]))
        act = self.env['mail.activity'].browse(act_id)
        return act.calendar_event_id.id

    @api.depends('start', 'duration')
    def _compute_stop(self):
        duration_field = self._fields['duration']
        self.env.remove_to_compute(duration_field, self)
        for event in self:
            event.stop = event.start + timedelta(minutes=round((event.duration or 1.0) * 60))
            if event.allday:
                event.stop -= timedelta(seconds=1)
