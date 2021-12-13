from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import logging

_logger = logging.getLogger(__name__)


class calendar_event(models.Model):
    _inherit = 'calendar.event'

    @api.model
    def _default_partners(self):
        return super(calendar_event, self)._default_partners()

    partner_sales_ids = fields.Many2many(
        'res.partner', 'calendar_event_res_partner_sales_rel',
        string='Attendees For Sales', default=_default_partners)
    rvd_image_ids = fields.One2many('rvd.meeting.image', 'meeting_id', string="Image")

    def button_action_submit(self):
        for calendar_meeting in self:
            name = calendar_meeting.meeting_mom
            remove_chars = ["<p>", "<br>", "</p>", " "]
            for remove in remove_chars:
                if name:
                    name = name.replace(remove, '')

            activity = self.env['mail.activity'].search([('meeting_id', '=', calendar_meeting.id)])
            if activity:
                if not name or not calendar_meeting.rvd_image_ids:
                    raise ValidationError(_("Please input result meeting"))
                else:
                    calendar_meeting.state = 'submit'
                    activity.action_done()
                    cal_meet = calendar_meeting.fal_estimated_cost
                    calendar_meeting.fal_last_estimated_cost = cal_meet

    def write(self, values):
        if 'partner_sales_ids' in values:
            values['attendee_ids'] = self._attendees_values(values['partner_sales_ids'])
        res = super(calendar_event, self).write(values)
        return res

    @api.model
    def create(self, values):
        res = super(calendar_event, self).create(values)
        # create attendee
        if values.get("partner_sales_ids"):
            calendar_event_obj = self.env['calendar.event']
            calendar_event_id = calendar_event_obj.search([
                ("id", '=', res.id)])
            calendar_event_id.write({
                'attendee_ids': self._attendees_values(values.get("partner_sales_ids"))})
        return res


class RvdUploadImage(models.Model):
    _name = 'rvd.meeting.image'

    name = fields.Char("Name")
    meeting_id = fields.Many2one('calendar.event', string='Meeting')
    document = fields.Binary(string="Document")