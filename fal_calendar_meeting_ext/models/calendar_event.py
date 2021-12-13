# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import email_split
import datetime
import uuid
import logging

_logger = logging.getLogger(__name__)
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT


class fal_meeting_type(models.Model):
    _name = 'fal.meeting.type'
    _description = "Meeting Type"

    name = fields.Char('Name', required=True)
    fal_mail_template_id = fields.Many2one(
        'mail.template', string='Mail Template for Invitation',
        domain=[('model', '=', 'calendar.attendee')])

# End of fal_meeting_type


class calendar_event(models.Model):
    _inherit = 'calendar.event'

    # Stage Workflow
    def button_action_cancel(self):
        for calendar_meeting in self:
            calendar_meeting.state = 'cancel'

    def button_action_draft(self):
        for calendar_meeting in self:
            calendar_meeting.state = 'draft'
            calendar_meeting.fal_meeting_sequence = False

    def button_action_submit(self):
        for calendar_meeting in self:
            calendar_meeting.state = 'submit'
            cal_meet = calendar_meeting.fal_estimated_cost
            calendar_meeting.fal_last_estimated_cost = cal_meet

    def button_action_validate(self):
        for calendar_meeting in self:
            calendar_meeting.state = 'validate'

    def button_action_confirm(self):
        for calendar_meeting in self:
            return {
                'name': _('Warning Message'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'calendar.event.warning.wizard',
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref(
                    'fal_calendar_meeting_ext.calendar_event_warning_wizard_form'
                ).id, 'form')],
                'target': 'new',
                'context': dict({'calendar_event_id': self.id}),
            }

    def button_action_close(self):
        for calendar_meeting in self:
            calendar_meeting.fal_last_actual_cost = self.fal_actual_cost
            calendar_meeting.state = 'closed'

    # Time & Cost Computation
    @api.onchange('fal_target_duration_gap')
    def _warning_target_duration_gap(self):
        if self.fal_target_duration_gap < 0:
            warning_mess = {
                'title': _('Target Duration is inconsistent.'),
                'message': _('Please check with meeting details.')
            }
            return {'warning': warning_mess}

    @api.depends(
        "partner_ids", "duration", 'state')
    def _compute_estimated_cost(self):
        for meeting in self:
            estimated_cost = 0
            for partner_id in meeting.partner_ids:
                if partner_id.fal_standard_rates.rates:
                    if meeting.allday:
                        rates = partner_id.fal_standard_rates.rates
                        estimated_cost += rates * 24
                    else:
                        rates = partner_id.fal_standard_rates.rates
                        estimated_cost += rates * meeting.duration
            meeting.fal_estimated_cost = estimated_cost

    @api.depends(
        "attendee_ids", 'fal_meeting_agenda_ids', 'fal_meeting_agenda_ids.actual_duration', 'fal_elapsed_time', 'state')
    def _compute_actual_cost(self):
        for meeting in self:
            actual_cost = 0
            for partner_id in meeting.attendee_ids:
                rates = partner_id.partner_id.fal_standard_rates.rates
                if rates and partner_id.effective_presence:
                    meet = meeting.fal_meeting_agenda_ids
                    actual_cost += sum(
                        float(
                            meting.actual_duration
                        ) for meting in meet if meting
                    ) * partner_id.partner_id.fal_standard_rates.rates
            meeting.fal_actual_cost = actual_cost

    @api.depends('fal_estimated_cost', 'fal_actual_cost')
    def _compute_cost_gap(self):
        for meeting in self:
            actual_cost = meeting.fal_actual_cost
            meeting.fal_cost_gap = actual_cost - meeting.fal_estimated_cost

    @api.depends("duration")
    def _compute_estimated_duration(self):
        if self.allday:
            self.fal_estimated_duration = 24
        else:
            self.fal_estimated_duration = self.duration

    @api.depends(
        'fal_meeting_agenda_ids', 'fal_meeting_agenda_ids.actual_duration',
        'fal_elapsed_time')
    def _compute_actual_duration(self):
        self.fal_actual_duration = self.fal_elapsed_time

    @api.depends(
        'fal_meeting_agenda_ids',
        'fal_meeting_agenda_ids.target_duration')
    def _compute_total_duration(self):
        meet_agenda = self.fal_meeting_agenda_ids
        self.fal_total_target_duration = round(sum(
            float(
                meeting_agenda_id.target_duration
            ) for meeting_agenda_id in meet_agenda if meeting_agenda_id), 2)

    @api.depends(
        'fal_meeting_agenda_ids', 'fal_meeting_agenda_ids.actual_duration')
    def _compute_total_actual_duration(self):
        meet_agenda = self.fal_meeting_agenda_ids
        self.fal_total_actual_duration = sum(
            float(
                meeting_agenda_id.actual_duration
            ) for meeting_agenda_id in meet_agenda if meeting_agenda_id)

    @api.depends('fal_total_target_duration', 'duration')
    def _compute_estimated_gap(self):
        if self.allday:
            self.fal_target_duration_gap = 24 - self.fal_total_target_duration
        else:
            target_duration = self.fal_total_target_duration
            self.fal_target_duration_gap = self.duration - target_duration

    @api.depends(
        'fal_total_target_duration', 'fal_meeting_agenda_ids',
        'fal_meeting_agenda_ids.actual_duration')
    def _compute_actual_gap(self):
        meet_agenda = self.fal_meeting_agenda_ids
        self.fal_actual_duration_gap = sum(
            float(
                meeting_agenda_id.actual_duration
            ) for meeting_agenda_id in meet_agenda if meeting_agenda_id
        ) - self.fal_total_target_duration

    def _get_action_url(self):
        if self.id:
            if 'allowed_company_ids' in request.env.context:
                cids = request.env.context['allowed_company_ids']
            else:
                cids = [request.env.company.id]
            action_url = '%s/web?db=%s#id=%s&menu_id=%s&action=%s&view_type=form&cids=%s' % (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url'),
                self.env.cr.dbname,
                self.id,
                self.env.ref('calendar.mail_menu_calendar').id,
                self.env.ref('calendar.action_calendar_event').id,
                cids,
            )
            self.fal_action_url = action_url
        else:
            self.fal_action_url = ''

    # Start Field Definition
    # Cost & Time Estimation vs Reality
    fal_estimated_cost = fields.Monetary(
        "Target Cost", compute=_compute_estimated_cost, store=True)
    fal_last_estimated_cost = fields.Monetary("Last Target Cost")
    fal_actual_cost = fields.Monetary(
        "Actual Cost", compute=_compute_actual_cost, store=True)
    fal_last_actual_cost = fields.Monetary("Last Actual Cost")
    fal_cost_gap = fields.Monetary(
        "Cost Gap", compute=_compute_cost_gap, store=True)
    fal_estimated_duration = fields.Float(
        "Estimated Duration", compute=_compute_estimated_duration)
    fal_actual_duration = fields.Float(
        "Actual Duration", compute=_compute_actual_duration)
    fal_total_target_duration = fields.Float(
        "Total Target Duration", compute=_compute_total_duration)
    fal_total_actual_duration = fields.Float(
        "Total Actual Duration", compute=_compute_total_actual_duration)
    fal_total_real_actual_duration = fields.Float(
        "Total Real Duration", copy=False)
    fal_target_duration_gap = fields.Float(
        "Target Duration Gap", compute=_compute_estimated_gap)
    fal_actual_duration_gap = fields.Float(
        "Actual Duration Gap", compute=_compute_actual_gap)
    duration = fields.Float(string="Target Duration")
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.user.company_id.currency_id)

    # Stage & Information
    fal_important_category = fields.Selection([
        ('important', 'Important'),
        ('normal', 'Normal'), ('low', 'Low')], "Important Category")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Done'),
        ('validate', 'Approved'),
        ('validate1', 'Second Approval'),
        ('open', 'Confirmed'),
        ('closed', 'Closed'),
        ('cancel', 'Cancel')
    ], string='Status', readonly=True, tracking=True, default='draft')
    fal_meeting_sequence = fields.Integer(
        "Meeting sequence", readonly=True,
        help="Showing how much validated meeting has been occured")
    meeting_mom = fields.Html(string="Internal MOM", help="Write meeting MOM here")
    fal_public_mom = fields.Html(string="Public MOM", help="Write public meeting MOM here")
    fal_meeting_type = fields.Many2one('fal.meeting.type', "Meeting Type")

    # Agenda
    fal_meeting_agenda_ids = fields.One2many(
        "fal.meeting.agenda", "calendar_event_id", "Agenda")

    # Real Stopwatch
    fal_start_time = fields.Datetime("Start Time")
    fal_elapsed_time = fields.Float("Elapsed Time")
    fal_stopwatch_status = fields.Selection([
        ('stop', 'Stopped'), ('start', 'Started'),
        ('pause', 'Paused')], "Stop watch status", default="stop")
    fal_use_agenda = fields.Boolean(string='Use Agenda')

    # URL
    fal_action_url = fields.Char('Action URL', compute="_get_action_url")
    # End Field Definition

    # Timer Stopwatch
    def start_timer(self):
        self.fal_stopwatch_status = 'start'
        self.fal_start_time = fields.Datetime.now()

    def pause_timer(self):
        to_allocate_time = self.fal_elapsed_time + round(int(((
            fields.Datetime.now() - self.fal_start_time
        ).seconds) / 60.0) / 60.0, 2)
        return {
            'name': _('Allocate Time'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'calendar.event.stop.timer.wizard',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref(
                'fal_calendar_meeting_ext.calendar_event_stop_timer_wizard_form').id, 'form')],
            'target': 'new',
            'context': dict({
                'calendar_event_id': self.id,
                'parent_partner_idsa': self.partner_ids.ids or False,
                'default_to_allocate_time': to_allocate_time or False,
                'pause_or_stop': 'pause'}),
        }

    def resume_timer(self):
        self.fal_stopwatch_status = 'start'
        self.fal_start_time = fields.Datetime.now()

    def stop_timer(self):
        to_allocate_time = self.fal_elapsed_time + round(int(((
            fields.Datetime.now() - self.fal_start_time
        ).seconds) / 60.0) / 60.0, 2)
        if self.fal_stopwatch_status == 'pause':
            to_allocate_time = self.fal_actual_duration

        return {
            'name': _('Allocate Time'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'calendar.event.stop.timer.wizard',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref(
                'fal_calendar_meeting_ext.calendar_event_stop_timer_wizard_form').id, 'form')],
            'target': 'new',
            'context': dict({
                'calendar_event_id': self.id,
                'parent_partner_idsa': self.partner_ids.ids or False,
                'default_to_allocate_time': to_allocate_time or False,
                'pause_or_stop': 'stop'}),
        }

    # Mail Meeting
    @api.model
    def message_new(self, msg_dict, custom_values=None):
        if custom_values is None:
            custom_values = {}

        meeting_subject = msg_dict.get('subject', '')
        meeting_body = msg_dict.get('body', '')
        mail = email_split(msg_dict.get('cc', False))

        date_start = datetime.datetime.now()
        start = date_start.strftime("%Y-%m-%d %H:%M:%S")
        date_stop = date_start + datetime.timedelta(hours=8)
        stop = date_stop.strftime("%Y-%m-%d %H:%M:%S")

        custom_values.update({
            'name': meeting_subject.strip(),
            'start': start,
            'stop': stop,
            'meeting_mom': meeting_body.strip(),
            'context': mail,
        })

        return super(calendar_event, self).message_new(msg_dict, custom_values)

    def get_partner_ids_internal(self):
        HrEmployee = self.env['hr.employee']
        res = []
        for partner in self.partner_ids:
            user_ids = partner.user_ids
            if user_ids:
                for user in user_ids:
                    employee_ids = HrEmployee.search([('user_id', '=', user.id)])
                    if employee_ids:
                        res.append(partner.id)
        return str(res).replace('[', '').replace(']', '')

    def get_partner_ids_public(self):
        return str([self.partner_ids.ids]).replace('[', '').replace(']', '')

    @api.model
    def create(self, values):
        res = super(calendar_event, self).create(values)

        if values.get("context"):
            mail_count = len(values.get("context"))
            res_partner_obj = request.env['res.partner']
            calendar_event_obj = request.env['calendar.event']

            value = 0
            calendar_event_id = calendar_event_obj.search([
                ("id", '=', res.id)])
            for data in range(0, mail_count):
                partner_id = res_partner_obj.search([
                    ('email', 'ilike', values.get("context")[value])], limit=1)

                if partner_id:
                    calendar_event_id.write({
                        'partner_ids': [(4, partner_id.id)]})
                value += 1

            partner_list = []
            for attendee_id in res.attendee_ids:
                if attendee_id.partner_id.id in partner_list:
                    raise UserError(_("There is duplicate attendees"))
                partner_list.append(attendee_id.partner_id.id)
            if res.fal_target_duration_gap < 0:
                raise UserError(_(
                    "Please Check between meeting duration and agenda duration you have"))
        return res
        _logger.info(res)

    def write(self, values):
        res = super(calendar_event, self).write(values)
        partner_list = []
        for attendee_id in self.attendee_ids:
            if attendee_id.partner_id.id in partner_list:
                raise UserError(_("There is duplicate attendees"))
            partner_list.append(attendee_id.partner_id.id)
        if self.fal_target_duration_gap < 0:
            raise UserError(_(
                "Please Check between meeting duration and agenda duration you have"))
        return res

    def action_sendmail(self):
        if self.fal_meeting_type.fal_mail_template_id:
            email = self.env.user.email
            partner = []
            if email:
                for meeting in self:
                    for attendee in meeting.attendee_ids:
                        partner.append(attendee.partner_id.id)
            template_id = self.fal_meeting_type.fal_mail_template_id.id
            ctx = {
                'default_model': 'calendar.attendee',
                'mail_post_autofollow': True,
                'default_composition_mode': 'comment',
                'default_use_template': True,
                'default_partner_ids': partner,
                'default_template_id': template_id,
                'force_email': True,
                'custom_layout': 'mail.mail_notification_light',
            }
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_id': self.id,
                'res_model': 'mail.compose.message',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }
        else:
            return super(calendar_event, self).action_sendmail()
# end of calendar_event


class Attendee(models.Model):
    _inherit = 'calendar.attendee'

    meeting_category = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')], 'Category',
        related="partner_id.fal_meeting_category")
    role = fields.Many2one("fal.meeting.role", "Role")
    presence_required = fields.Many2one(
        "fal.meeting.presence.required", "Presence Required")
    effective_presence = fields.Boolean("Effective Presence")


class fal_meeting_presence_required(models.Model):
    _name = 'fal.meeting.presence.required'
    _description = "Meeting Presence"

    name = fields.Char("Name")


class fal_meeting_role(models.Model):
    _name = 'fal.meeting.role'
    _description = "Meeting Role"

    name = fields.Char("Name")


class fal_meeting_agenda(models.Model):
    _name = 'fal.meeting.agenda'
    _description = "Meeting Agenda"
    _order = "name"

    calendar_event_id = fields.Many2one("calendar.event", "Meeting")
    calendar_event_state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submitted'),
        ('validate', 'Approved'),
        ('validate1', 'Second Approval'),
        ('open', 'Confirmed'),
        ('closed', 'Closed'),
        ('cancel', 'Cancel')], related="calendar_event_id.state")
    name = fields.Char("Subject", required=True)
    partner_id = fields.Many2one("res.partner", "Speaker")
    target_duration = fields.Float("Target Duration")
    actual_duration = fields.Float("Actual Duration")
