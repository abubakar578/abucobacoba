# -*- coding: utf-8 -*-
from odoo import api, fields, models


class FalResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    alias_prefix = fields.Char('Default Alias Name for Meeting')
    fal_alias_domain = fields.Char(
        'Alias Domain',
        default=lambda self: self.env[
            "ir.config_parameter"].get_param("mail.catchall.domain"))
    no_auto_email = fields.Boolean(
        'Block Automatic Invitation to Attendee(s)',
        default=lambda self: self.env[
            "ir.config_parameter"].get_param("calendar.block_mail"))

    @api.model
    def get_values(self):
        res = super(FalResConfigSettings, self).get_values()
        alias_name = self.env.ref(
            'fal_calendar_meeting_ext.mail_alias_meeting').alias_name
        no_auto_email = self.env[
            "ir.config_parameter"].get_param("calendar.block_mail", False)
        res.update(
            alias_prefix=alias_name,
            no_auto_email=no_auto_email,
        )
        return res

    def set_values(self):
        res = super(FalResConfigSettings, self).set_values()
        for record in self:
            self.env.ref(
                'fal_calendar_meeting_ext.mail_alias_meeting').sudo().write(
                {'alias_name': record.alias_prefix})
            self.env['ir.config_parameter'].set_param('calendar.block_mail', record.no_auto_email)
        return res
