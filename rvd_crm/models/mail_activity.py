from collections import defaultdict
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import logging
import pytz

from odoo import api, exceptions, fields, models, _
from odoo.osv import expression
from odoo.exceptions import ValidationError

from odoo.tools.misc import clean_context
from odoo.addons.base.models.ir_model import MODULE_UNINSTALL_FLAG

_logger = logging.getLogger(__name__)


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    # ------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------

    # Override
    @api.model
    def _default_activity_type_id(self):
        ActivityType = self.env["mail.activity.type"]
        activity_type_todo = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        default_vals = self.default_get(['res_model_id', 'res_model'])
        if not default_vals.get('res_model_id'):
            return ActivityType
        current_model_id = default_vals['res_model_id']
        current_model = default_vals['res_model']
        # if current_model == 'crm.lead':
        #     ActivityMeeting = ActivityType.search([('category', '=', 'meeting')], limit=1)
        #     return ActivityMeeting
        if activity_type_todo and activity_type_todo.active and (activity_type_todo.res_model_id.id == current_model_id or not activity_type_todo.res_model_id):
            return activity_type_todo
        activity_type_model = ActivityType.search([('res_model_id', '=', current_model_id)], limit=1)
        if activity_type_model:
            return activity_type_model
        activity_type_generic = ActivityType.search([('res_model_id','=', False)], limit=1)
        return activity_type_generic

    # @api.onchange('res_model', 'activity_category')
    # def _onchange_activity_type(self):
    #     if self.res_model == 'crm.lead':
    #         return {'domain': {'activity_type_id': [('category', '=', 'meeting')]}}

    activity_type_id = fields.Many2one(
        'mail.activity.type', string='Activity Type',
        domain="['|', ('res_model_id', '=', False), ('res_model_id', '=', res_model_id)]", ondelete='restrict',
        default=_default_activity_type_id)



    @api.constrains('start')
    def _check_start_meeting(self):
        for meeting in self:
            leader_user = self.env['crm.team'].search([('user_id', '=', self.env.uid)])
            if meeting.activity_type_id.category == 'meeting':
                if meeting.start < fields.Datetime.today() or meeting.start == fields.Datetime.today() and not leader_user:
                    raise ValidationError(
                    _('The start date cannot be less than the date now.'))
            else:
                if meeting.date_deadline < fields.Date.today() or meeting.date_deadline == fields.Date.today() and not leader_user:
                    raise ValidationError(
                    _('The start date cannot be less than the date now.'))

    @api.model
    def create(self, values):
        activity = super(MailActivity, self).create(values)
        # post message on activity, after creating it
        record = self.env[activity.res_model].browse(activity.res_id)
        record.message_post(
            body="Activity %s: %s Created" % (activity.res_name or '', activity.summary or ''),
            mail_activity_type_id=activity.activity_type_id.id,
        )
        return activity

    def write(self, values):
        res = super(MailActivity, self).write(values)
        # post message on activity, after modifying it
        record = self.env[self.res_model].browse(self.res_id)
        record.message_post(
            body="Activity %s: %s Modified" % (self.res_name or '', self.summary or ''),
            mail_activity_type_id=self.activity_type_id.id,
        )
        return res
