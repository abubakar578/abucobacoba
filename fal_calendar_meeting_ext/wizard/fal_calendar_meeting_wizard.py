# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import datetime
from odoo.tools.misc import formatLang
import logging

_logger = logging.getLogger(__name__)


class calendar_event_warning_wizard(models.TransientModel):
    _name = 'calendar.event.warning.wizard'
    _description = 'Calendar Event Warning'

    @api.depends("calendar_event_id")
    def _generate_warning_message(self):
        for cal_event in self:
            amount_text = formatLang(self.env, cal_event.calendar_event_id.fal_estimated_cost, currency_obj=cal_event.calendar_event_id.currency_id)
            cal_event.warning_msg = \
                "The estimated cost is " + str(amount_text) + " and " + str(len(
                    cal_event.calendar_event_id.partner_ids)
                ) + " persons will attend. \
                Is this meeting necessary for your activity?"

    @api.depends("calendar_event_id")
    def _generate_estimated_cost(self):
        for calendar_event_warning_wiz in self:
            calendar_event_warning_wiz.calendar_event_estimated_cost =\
                calendar_event_warning_wiz.calendar_event_id.fal_estimated_cost

    calendar_event_id = fields.Many2one(
        "calendar.event", "Calendar ID",
        default=lambda s: s._context['calendar_event_id'])
    calendar_event_estimated_cost = fields.Float(
        'Calendar Estimated Cost', compute=_generate_estimated_cost)
    warning_msg = fields.Char(
        "Warning Message", compute=_generate_warning_message)

    def confirm_meeting(self):
        for calendar_event in self:
            calendar_event.calendar_event_id.fal_meeting_sequence =\
                self.env['calendar.event'].search([
                    ('state', '=', 'open'),
                    ('fal_meeting_sequence', '!=', False)
                ], order="fal_meeting_sequence desc", limit=1
                ).fal_meeting_sequence + 1 or 1
            calendar_event.calendar_event_id.fal_last_estimated_cost =\
                calendar_event.calendar_event_estimated_cost
            calendar_event.calendar_event_id.state = "open"

    def _prepare_analytic_line_vals(
        self, unit_amount, date_from,
        i, sheet_obj, employee_id_obj,
        calendar
    ):
        self.ensure_one()
        val_y = employee_id_obj.fal_leave_timesheet_analytic_account_id
        if not val_y:
            raise UserError(_(
                'Please Fill Employee Leave \
                Timesheet Analytic Account First.'))
        hol = calendar
        project = employee_id_obj.fal_leave_project_id
        if not project:
            raise UserError(_(
                'Please Fill Employee Leave \
                Project First.'))
        partner = employee_id_obj.user_id
        return {
            'name': hol.name,
            'date': date_from + datetime.timedelta(days=i),
            'unit_amount': unit_amount,
            'account_id': val_y and val_y.id,
            'is_timesheet': True,
            'user_id': employee_id_obj.user_id.id,
            'partner_id': partner and partner.id,
            'project_id': project.id,
            'sheet_id': sheet_obj.id
        }


class calendar_event_add_invitation_wizard(models.TransientModel):
    _name = "calendar.event.add.invitation.wizard"
    _description = "Calendar Event Add"

    calendar_event_id = fields.Many2one(
        "calendar.event", "Calendar ID",
        default=lambda s: s._context['active_ids'])
    partner_id = fields.Many2one('res.partner', 'Contact')

    def create_invitation(self):
        for calendar_event_wizard in self:
            for calendar_event in self.env['calendar.event'].browse(
                self._context['active_ids']
            ):
                partner = calendar_event_wizard.partner_id
                if partner not in calendar_event.partner_ids:
                    values = {
                        'partner_id': calendar_event_wizard.partner_id.id,
                        'event_id': calendar_event.id,
                        'email': calendar_event_wizard.partner_id.email,
                    }
                    calendar_event.env['calendar.attendee'].create(values)


class calendar_event_stop_timer_wizard(models.TransientModel):
    _name = 'calendar.event.stop.timer.wizard'
    _description = "Calendar Event Stop"

    @api.model
    def _fill_time_to_allocate(self):
        if self._context.get('active_ids', False):
            return self.env['calendar.event'].browse(
                self._context['calendar_event_id']
            ).fal_elapsed_time + round(int(((
                    fields.Datetime.now() - self.env['calendar.event'].browse(
                    self.env.context.get('active_ids')
                    ).fal_start_time).seconds) / 60.0) / 60.0, 2)

    @api.model
    def _fill_meeting_agenda_temporary(self):
        if self._context.get('active_ids', False):
            fill_agenda_temporary = []
            for agenda in self.env['calendar.event'].browse(
                self._context['calendar_event_id']
            ).fal_meeting_agenda_ids:
                fill_agenda_temporary.append((
                    0, 0, {
                        'calendar_event_stop_timer_wizard_id': self.id,
                        'agenda_id': agenda.id,
                        'agenda_actual_duration': agenda.actual_duration,
                        'agenda_name': agenda.name,
                        'agenda_partner_id': agenda.partner_id,
                        'agenda_target_duration': agenda.target_duration}))
            return fill_agenda_temporary

    @api.model
    def _fill_partner_ids(self):
        if self._context.get('active_ids', False):
            return [(6, 0, self.env['calendar.event'].browse(
                self._context['calendar_event_id']).partner_ids.ids)]

    to_allocate_time = fields.Float("Time to Allocates")
    partner_ids = fields.Many2many(
        "res.partner", default=_fill_partner_ids)
    calendar_event_wizard_agenda_temporary_ids = fields.One2many(
        'calendar.event.warning.agenda.temporary',
        'calendar_event_stop_timer_wizard_id',
        'Temporary Agenda', default=_fill_meeting_agenda_temporary)

    def confirm_time_allocation(self):
        total_agenda_time = 0
        for agenda in self.calendar_event_wizard_agenda_temporary_ids:
            total_agenda_time += float(agenda.agenda_actual_duration)
        temporary_agenda = self.calendar_event_wizard_agenda_temporary_ids
        for agenda_temporary in temporary_agenda:
            agenda_temporary.agenda_id.write(
                {'actual_duration': agenda_temporary.agenda_actual_duration})
        self.env['calendar.event'].browse(self._context.get(
            'active_ids')).fal_stopwatch_status = self._context.get(
                'pause_or_stop', 'start')
        self.env['calendar.event'].browse(self._context.get(
            'active_ids')).fal_elapsed_time = self.to_allocate_time


class calendar_event_wizard_agenda_temporary(models.TransientModel):
    _name = 'calendar.event.warning.agenda.temporary'
    _description = "Calendar Event Warning"

    calendar_event_stop_timer_wizard_id = fields.Many2one(
        "calendar.event.stop.timer.wizard", "Calendar Wizard ID")
    agenda_id = fields.Many2one('fal.meeting.agenda', 'Agenda')
    agenda_name = fields.Char("Subject")
    agenda_partner_id = fields.Many2one("res.partner", "Speaker")
    agenda_target_duration = fields.Float("Target Duration")
    agenda_actual_duration = fields.Float('Actual Duration')
