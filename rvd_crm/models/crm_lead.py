# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.addons.crm.models import crm_stage
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
import base64
import io
import re
import logging

_logger = logging.getLogger(__name__)


class Lead(models.Model):
    _inherit = "crm.lead"
    _description = "Lead/Opportunity"

    rvd_req_lots = fields.Boolean('Request Lost', default=False, readonly=True)
    rvd_done_lost = fields.Boolean('Done Lost', default=False)
    is_read = fields.Boolean('Is Read', default=False)
    is_draft = fields.Boolean('Is Draft', default=True)
    is_quotation = fields.Boolean('Quotation', default=False)
    rvd_invoice = fields.Boolean('Invoice', compute='_check_invoice')
    can_edit_form = fields.Boolean('Can Edit', default=True)
    is_done_reply = fields.Boolean('Reply', compute='_compute_check_reply')

    rvd_crm_status = fields.Selection([
        ('hot', 'Hot'),
        ('warm', 'Warm'),
        ('cold', 'Cold')], string='Status', default='warm')
    rvd_customer_by = fields.Selection([
        ('walkin', 'Walk In'),
        ('phone', 'Phone'),
        ('wa', 'WhatsApp'),
        ('email', 'Email'),
        ('visit', 'Visit'),
        ('fax', 'Fax')], string='Customer By', default='email')
    sales_admin_id = fields.Many2one('res.users', string='CSS', tracking=True)
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, tracking=True)
    enquiry_ids = fields.One2many('customer.enquiry.line', 'lead_id', string='Customer Enquiry', copy=False)
    activity_ids = fields.One2many(tracking=True)
    message_ids = fields.One2many(tracking=True)
    date_deadline = fields.Date(tracking=True)
    priority = fields.Selection(
        crm_stage.AVAILABLE_PRIORITIES, string='Priority', index=True,
        default=crm_stage.AVAILABLE_PRIORITIES[1][0], required=True)
    stage_id = fields.Many2one(
        'crm.stage', string='Stage', index=True, tracking=True,
        compute='_compute_stage_id', readonly=True, store=True,
        copy=False, group_expand='_read_group_stage_ids', ondelete='restrict',
        domain="['|', ('team_id', '=', False), ('team_id', '=', team_id)]")
    enquiry_file = fields.Binary('File Enquiry')
    file_name_enquiry = fields.Char("FIle Name Enquiry")

    def _compute_check_reply(self):
        for lead in self:
            message_id = self.env['mail.message'].search([
                ('author_id', '=', lead.partner_id.id),
                ('message_type', '=', 'email'),
                ('subtype_id', '=', self.env.ref('mail.mt_comment').id),
                ('res_id', '=', lead.id),
                ('model', '=', 'crm.lead'),
                ('notification_ids', '!=', False),
            ], limit=1)
            if message_id:
                lead.is_done_reply = True
                if lead.stage_id == self.env.ref('rvd_crm.stage_outstanding_draft'):
                    lead.stage_id = self.env.ref('crm.stage_lead1')
            else:
                lead.is_done_reply = False

    def _compute_can_edit_view(self):
        for lead in self:
            stage_peluang = self.env.ref('rvd_crm.stage_outstanding_draft')
            stage_gagal = self.env.ref('rvd_crm.stage_lost')
            stage_list = [stage_peluang.id, stage_gagal.id]

            can_edit = False
            if self._uid in self.env.ref('rvd_crm.group_no_member').users.ids and not self.stage_id.id in stage_list:
                lead.can_edit_form = True
            if self._uid in self.env.ref('rvd_crm.group_sales_person').users.ids and not self.stage_id.id in stage_list:
                lead.can_edit_form = True
            elif self.stage_id.id in stage_list:
                lead.can_edit_form = True
            else:
                lead.can_edit_form = False

    @api.depends('team_id', 'type', 'order_ids', 'order_ids.state', 'enquiry_ids', 'activity_ids', 'message_attachment_count')
    def _compute_stage_id(self):
        for lead in self:
            # stage
            stage_permohonan = self.env.ref('crm.stage_lead1')
            stage_quoted = self.env.ref('crm.stage_lead2')
            stage_proses = self.env.ref('crm.stage_lead3')
            stage_won = self.env.ref('crm.stage_lead4')
            stage_peluang = self.env.ref('rvd_crm.stage_outstanding_draft')
            stage_follow_up = self.env.ref('rvd_crm.stage_follow_up')

            record_crm = self.env['record.crm']
            # search attachment
            groups_sales_person_id = self.env.ref('rvd_crm.group_sales_person')
            groups_sales_admin_id = self.env.ref('rvd_crm.group_no_member')
            groups_sales_person = self.env['res.groups'].browse(groups_sales_person_id.id)
            groups_sales_admin = self.env['res.groups'].browse(groups_sales_admin_id.id)
            record_crm = self.env['record.crm']

            # # process
            if not lead.stage_id:
                # if any(sales.id == lead._uid for sales in groups_sales_admin.users):
                if self._uid in self.env.ref('rvd_crm.group_no_member').users.ids:
                    lead.stage_id = stage_permohonan
                else:
                    lead.stage_id = lead._stage_find(domain=[('fold', '=', False)]).id
            # set stage
            # if any(sales.id == lead._uid for sales in groups_sales_admin.users):
            #     tracking = lead._prepare_tracking_stage(lead.id, lead.stage_id, stage_permohonan.id)
            #     record_crm.create(tracking)
            #     lead.stage_id = stage_permohonan
            # peluang to permohonan
            elif lead.stage_id == stage_peluang:
                if lead.enquiry_file or lead.is_done_reply:
                    tracking = self._prepare_tracking_stage(lead.id, lead.stage_id, stage_permohonan.id)
                    record_crm.create(tracking)
                    lead.stage_id = stage_permohonan
            # permohonan penawaran to proses penawaran
            # elif lead.enquiry_ids and lead.stage_id == stage_permohonan:
            #     tracking = self._prepare_tracking_stage(lead.id, lead.stage_id, stage_proses.id)
            #     record_crm.create(tracking)
            #     _logger.info("XXXXXXXXXXX")
            #     lead.stage_id = stage_proses
            #     lead.is_quotation = True
            # proses to quoted
            elif any(order.state == 'draft' for order in lead.order_ids) and lead.stage_id == stage_proses:
                tracking = self._prepare_tracking_stage(lead.id, lead.stage_id, stage_quoted.id)
                record_crm.create(tracking)
                lead.stage_id = stage_quoted
                lead.is_quotation = False
            # quoted to follow up
            elif lead.activity_ids and lead.stage_id == stage_quoted:
                tracking = self._prepare_tracking_stage(lead.id, lead.stage_id, stage_follow_up.id)
                record_crm.create(tracking)
                lead.stage_id = stage_follow_up
            # to berhasil
            elif lead.order_ids:
                for order in lead.order_ids:
                    if order.state == 'sale' and lead.stage_id == stage_follow_up:
                        tracking = self._prepare_tracking_stage(lead.id, lead.stage_id, stage_won.id)
                        record_crm.create(tracking)
                        lead.stage_id = stage_won
                    elif order.state == 'sale' and lead.stage_id == stage_quoted:
                        tracking = self._prepare_tracking_stage(lead.id, lead.stage_id, stage_won.id)
                        record_crm.create(tracking)
                        lead.stage_id = stage_won

    # default sales admin
    @api.onchange('partner_id', 'partner_id.sales_admin_id', 'user_id')
    def _onchange_sales_admin(self):
        if self.partner_id or self.user_id:
            relation = self.env['rvd.relation.sales'].search([('sales_person', '=', self.user_id.id)], limit=1)
            groups_admin = self.env['res.groups'].search([('name', '=', 'CSS')], limit=1)
            if relation:
                self.sales_admin_id = relation.sales_admin_ids[0].id
                return {'domain': {'sales_admin_id': [('id', '=', groups_admin.users.ids)]}}
            else:
                if self._uid in self.env.ref('rvd_crm.group_no_member').users.ids and not self.sales_admin_id:
                    self.user_id = False
                    self.sales_admin_id = self._uid
                    return {'domain': {'sales_admin_id': [('id', '=', groups_admin.users.ids)]}}


    @api.onchange('message_attachment_count', 'message_main_attachment_id')
    def _onchange_attch(self):
        stage_permohonan = self.env.ref('crm.stage_lead1')
        stage_proses = self.env.ref('crm.stage_lead3')
        record_obj = self.env['record.crm']
        if self.message_attachment_count > 0 and self.stage_id == stage_permohonan:
            tracking = self._prepare_tracking_stage(self.id, self.stage_id, stage_proses.id)
            record_obj.create(tracking)
            self.stage_id = stage_proses
            self.is_quotation = True

    @api.onchange('sales_admin_id')
    def _onchange_sales_domain(self):
        if self.partner_id or self.user_id:
            groups_person = self.env['res.groups'].search([('name', '=', 'Sales Person')], limit=1)
            if groups_person:
                return {'domain': {'user_id': [('id', '=', groups_person.users.ids)]}}

    @api.depends('order_ids', 'order_ids.invoice_ids')
    def _check_invoice(self):
        for item in self:
            if any(order.invoice_ids for order in self.order_ids):
                item.action_archive()
                item.rvd_invoice = True
            else:
                item.rvd_invoice = False

    def action_to_lost_sales(self):
        res = self.action_archive()
        stage_lost = self.env.ref('rvd_crm.stage_lost')
        self.write({
            'stage_id': stage_lost.id,
            'rvd_done_lost': True
        })
        return res

    def mark_as_read(self):
        stage_proses = self.env.ref('crm.stage_lead3')
        stage_permohonan = self.env.ref('crm.stage_lead1')
        if self.stage_id == stage_permohonan:
            self.write({
                'stage_id': stage_proses.id,
                'is_read': True,
                'is_draft': False,
            })
        return

    def action_set_lost(self, **additional_values):
        # Override
        if additional_values:
            additional_values.update({'rvd_req_lots': True})
            self.write(dict(additional_values))
        return


    def write(self, vals):
        write_result = super(Lead, self).write(vals)
        # stage
        stage_permohonan = self.env.ref('crm.stage_lead1')
        stage_peluang = self.env.ref('rvd_crm.stage_outstanding_draft')
        stage_proses = self.env.ref('crm.stage_lead3')

        record_crm = self.env['record.crm']
        if vals.get('rvd_customer_by') or vals.get('name'):
            display_name = self.name.split("/")
            name = False

            if vals.get('rvd_customer_by') == 'wa':
                if len(display_name) > 1:                        
                    name = 'CHAT/' + display_name[1]
                else:
                    name = 'CHAT/' + self.name
            elif vals.get('rvd_customer_by') == 'email':
                if len(display_name) > 1:                        
                    name = 'EMAIL/' + display_name[1]
                else:
                    name = 'EMAIL/' + self.name
            elif vals.get('rvd_customer_by') == 'walkin' or vals.get('rvd_customer_by') == 'fax' or vals.get('rvd_customer_by') == 'phone' or vals.get('rvd_customer_by') == 'visit':
                if len(display_name) > 1:                        
                    name = 'DIRECT/' + display_name[1]
                else:
                    name = 'DIRECT/' + self.name

            _logger.info(name)
            if name:
                if vals.get('name'):
                    vals.update({'name': name.upper()})
                else:
                    self.name = name.upper()

        if vals.get('enquiry_file'):
            crm_attachment = self.env['ir.attachment'].with_context(no_document=True).create({
                'name': vals.get('file_name_enquiry'),
                'type': 'binary',
                'datas': vals.get('enquiry_file'),
                'res_model': 'crm.lead',
                'res_id': self.id,
            })
            if crm_attachment and self.stage_id == stage_peluang:
                tracking = self._prepare_tracking_stage(self.id, self.stage_id, stage_permohonan.id)
                record_crm.create(tracking)
                self.stage_id = stage_permohonan

        if vals.get('enquiry_ids'):
            if vals.get('enquiry_ids') and self.stage_id == stage_permohonan or self.stage_id == stage_peluang:
                tracking = self._prepare_tracking_stage(self.id, self.stage_id, stage_proses.id)
                record_crm.create(tracking)
                self.stage_id = stage_proses
                self.is_quotation = True

        return write_result

    @api.model_create_multi
    def create(self, vals_list):
        leads = super(Lead, self).create(vals_list)
        attch_obj = self.env['ir.attachment']
        crm_attachment = False
        for vals in vals_list:
            # CUSTOMER BY
            if leads.rvd_customer_by:
                if leads.rvd_customer_by == 'wa':
                    leads.write({'name': 'CHAT/' + leads.name.upper()})
                elif leads.rvd_customer_by == 'walkin' or leads.rvd_customer_by == 'fax' or leads.rvd_customer_by == 'phone' or leads.rvd_customer_by == 'visit':
                    leads.write({'name': 'DIRECT/' + leads.name.upper()})
            # attachment
            attachment = attch_obj.search([('res_model', '=', 'crm.lead'), ('res_id', '=', leads.id)], limit=1)
            if attachment:
                leads.write({'enquiry_file': attachment.datas})
            # attachment enquiry
            else:
                if vals.get('enquiry_file'):
                    crm_attachment = self.env['ir.attachment'].with_context(no_document=True).create({
                        'name': vals.get('file_name_enquiry'),
                        'type': 'binary',
                        'datas': vals.get('enquiry_file'),
                        'res_model': 'crm.lead',
                        'res_id': leads.id
                    })

            stage_permohonan = self.env.ref('crm.stage_lead1')
            stage_peluang = self.env.ref('rvd_crm.stage_outstanding_draft')
            stage_proses = self.env.ref('crm.stage_lead3')
            groups_sales_admin_id = self.env.ref('rvd_crm.group_no_member')
            groups_sales_admin = self.env['res.groups'].browse(groups_sales_admin_id.id)
            record_crm = self.env['record.crm']

            stage_list = [stage_permohonan.id, stage_peluang.id]

            if vals.get('enquiry_ids'):
                if vals.get('enquiry_ids') and not vals.get('stage_id'):
                    tracking = self._prepare_tracking_stage(self.id, stage_permohonan, stage_proses.id)
                    record_crm.create(tracking)
                    leads.write({
                            'stage_id': stage_proses.id,
                            'is_quotation': True,
                        })

        return leads

    @api.model
    def _change_status(self):
        current_date = fields.Datetime.today()
        stage_quoted = self.env.ref('crm.stage_lead2')
        stage_follow_up = self.env.ref('rvd_crm.stage_follow_up')
        crm_lead_ids = self.env['crm.lead'].search([
            ('__last_update', '<=', current_date),
            ('stage_id', '=', stage_quoted.id),
        ])
        for crm in crm_lead_ids:
            last_update = crm.date_last_stage_update.strftime("%d")
            result_day = int(current_date.strftime("%d")) - int(last_update)
            if result_day >= 2 and crm.rvd_crm_status == 'hot':
                crm.color = 1
            elif result_day >= 3 and crm.rvd_crm_status == 'warm':
                crm.color = 1
            elif result_day >= 4 and crm.rvd_crm_status == 'cold':
                crm.color = 1

    def _prepare_tracking_stage(self, crm_id, old_stage, new_stage):
        return {
            'crm_lead_id': crm_id,
            'old_stage': old_stage.id,
            'new_stage': new_stage,
            'old_date': self.date_last_stage_update,
            'new_date': fields.Datetime.now(),
        }

    # override reply email
    # def _message_get_suggested_recipients(self):
    #     recipients = super(Lead, self)._message_get_suggested_recipients()
    #     try:
    #         for lead in self:
    #             if lead.partner_id:
    #                 if lead.stage_id == self.env.ref('rvd_crm.stage_outstanding_draft').id:
    #                     lead.write({'stage_id': self.env.ref('rvd_crm.stage_lead1').id})
    #                 lead._message_add_suggested_recipient(recipients, partner=lead.partner_id, reason=_('Customer'))
    #             elif lead.email_from:
    #                 if lead.stage_id == self.env.ref('rvd_crm.stage_outstanding_draft').id:
    #                     lead.write({'stage_id': self.env.ref('rvd_crm.stage_lead1').id})
    #                 lead._message_add_suggested_recipient(recipients, email=lead.email_from, reason=_('Customer Email'))
    #     except AccessError:  # no read access rights -> just ignore suggested recipients because this imply modifying followers
    #         pass
    #     return recipients

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        # remove external users
        if self.env.user.has_group('base.group_portal'):
            self = self.with_context(default_user_id=False)
        # remove default author when going through the mail gateway. Indeed we
        # do not want to explicitly set user_id to False; however we do not
        # want the gateway user to be responsible if no other responsible is
        # found.
        if self._uid == self.env.ref('base.user_root').id:
            self = self.with_context(default_user_id=False)

        if custom_values is None:
            custom_values = {}

        # check company
        stage_responded = self.env.ref('crm.stage_lead3')
        if msg_dict.get('from'):
            domain = msg_dict.get('from').split('@')
            email_domain = domain[1]
            if '>' in email_domain:
                check_domain = email_domain.split('>')
                email_domain = check_domain[0]
            company_partner_id = self.env['res.partner'].search([('email_domain', '=', email_domain)], limit=1)
            if company_partner_id:
                defaults = {
                    'name': "EMAIL/" + msg_dict.get('subject') or _("No Subject"),
                    'email_from': msg_dict.get('from'),
                    'partner_id': company_partner_id.id or False,
                    'stage_id': stage_responded.id,
                    'user_id': company_partner_id.user_id.id or False,
                    'sales_admin_id': company_partner_id.sales_admin_id.id,
                }
            else:
                defaults = {
                    'name': "EMAIL/" + msg_dict.get('subject') or _("No Subject"),
                    'email_from': msg_dict.get('from'),
                    'partner_id': msg_dict.get('author_id', False),
                }

        if msg_dict.get('priority') in dict(crm_stage.AVAILABLE_PRIORITIES):
            defaults['priority'] = msg_dict.get('priority')
        defaults.update(custom_values)
        # assign right company
        if 'company_id' not in defaults and 'team_id' in defaults:
            defaults['company_id'] = self.env['crm.team'].browse(defaults['team_id']).company_id.id

        return super(Lead, self).message_new(msg_dict, custom_values=defaults)

    def action_new_quotation(self):
        res = super(Lead, self).action_new_quotation()
        context = res.get('context')
        if self.enquiry_ids:
            enquiry = self.enquiry_ids
            enquiry = self._prepare_customer_enquiry(self.enquiry_ids)

            context.update({'default_enquiry_ids': enquiry})
        return res


    def _prepare_customer_enquiry(self, enquiry_list):
        temp = []
        for enquiry in enquiry_list:
            temp.append((0, 0, {
                'rvd_sku': enquiry.rvd_sku,
                'rvd_equipment_id': enquiry.rvd_equipment_id.id,
                'is_attribute': enquiry.is_attribute,
                'quantity': enquiry.quantity,
                'with_prio': enquiry.with_prio,
                'attr_desc': enquiry.attr_desc,
                'attr_model': enquiry.attr_model,
                'attr_detail': enquiry.attr_detail,
                'attr_gasket_type': enquiry.attr_gasket_type,
                'attr_height_min': enquiry.attr_height_min,
                'attr_height2_min': enquiry.attr_height2_min,
                'attr_od_min': enquiry.attr_od_min,
                'attr_od2_min': enquiry.attr_od2_min,
                'attr_id_min': enquiry.attr_id_min,
                'attr_id2_min': enquiry.attr_id2_min,
                'attr_gasket_od_min': enquiry.attr_gasket_od_min,
                'attr_flange_hat_min': enquiry.attr_flange_hat_min,
                'attr_lenght_min': enquiry.attr_lenght_min,
                'attr_lenght2_min': enquiry.attr_lenght2_min,
                'attr_widht_min': enquiry.attr_widht_min,
                'attr_widht2_min': enquiry.attr_widht2_min,
                'attr_litre_min': enquiry.attr_litre_min,
                'attr_ampere_min': enquiry.attr_ampere_min,
                'attr_bowl_thread_size_min': enquiry.attr_bowl_thread_size_min,
                'attr_thread_min': enquiry.attr_thread_min,
                'attr_thread_nut_min': enquiry.attr_thread_nut_min,
            }))

        return temp


    def action_count_meeting(self):
        stage_won = self.env.ref('crm.stage_lead4')
        stage_lost = self.env.ref('rvd_crm.stage_lost')

        dt_now = fields.Date.today()
        last_dt = fields.Datetime.today() - timedelta(days=1)
        mail_obj = self.env['mail.mail']
        for lead in self.search([('stage_id', '!=', stage_won.id or stage_lost.id)]).filtered(lambda x: len(x.activity_ids.filtered(lambda a: a.activity_type_id.category == 'meeting' and a.create_date == dt_now)) < 3):
            # create email and send now
            admin = self.env.ref('base.partner_admin')
            mail_body = _("""
                <b>Please you check</b>
                <p>Lead Name: %s</p>
                <br/>
                <p>please follow up in lead %s, you must be create meeting</p>
                """) % (lead.name, lead.name)
            mail = mail_obj.create({
                'subject': 'Please Check Lead: %s ' % (lead.name),
                'author_id': admin.id,
                'email_from': admin.email,
                'email_to': lead.user_id.email,
                'body_html': mail_body,
            }).send()

    def search_by_attr(self):
        context = dict(self.env.context)
        context.update({'is_attribute': True, 'prior_brand_ids': self.partner_id.prior_brand_ids.ids, 'with_prio': True, 'lead_id': self.id})
        view = self.env.ref('rvd_sale.view_search_attribute_create')
        return {
            'name': _('Attributes Product'),
            'res_model': 'customer.enquiry.line',
            'type': 'ir.actions.act_window',
            'views': [(view.id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }


class CustomerEnquiry(models.Model):
    _inherit = 'customer.enquiry.line'

    lead_id = fields.Many2one('crm.lead', 'Lead Opportunity')
    is_from_lead = fields.Boolean("Lead")

    def create_attrs(self):
        context = self._context
        if context.get('active_model') == 'crm.lead':
            self.write({
                'lead_id': context.get('active_id'),
                'is_attribute': True,
                'is_from_lead': True,
            })
            return
        else:
            res = super(CustomerEnquiry, self).create_attrs()
            return


    def action_open_attrs(self):
        return super(CustomerEnquiry, self).action_open_attrs()


    def search_product(self):
        context = self.env.context
        # res_context = res.get('context')
        code_obj = self.env['rvd.product.code']
        att_obj = self.env['rvd.product.attribute']
        context = dict(self.env.context)

        codes_list = []
        code_available = []
        result = []
        if context.get('lead_id'):
            if self.is_attribute or context.get('is_attribute'):
                # result range min and max

                min_od = self.attr_od_min - self.attr_od_max
                max_od = self.attr_od_min + self.attr_od_max
                min_id = self.attr_id_min - self.attr_id_max
                max_id = self.attr_id_min + self.attr_id_max

                min_od2 = self.attr_od2_min - self.attr_od2_max
                max_od2 = self.attr_od2_min + self.attr_od2_max
                min_id2 = self.attr_id2_min - self.attr_id2_max
                max_id2 = self.attr_id2_min + self.attr_id2_max

                widht_min = self.attr_widht_min - self.attr_widht_max
                widht_max = self.attr_widht_min + self.attr_widht_max
                widht2_min = self.attr_widht2_min - self.attr_widht2_max
                widht2_max = self.attr_widht2_min + self.attr_widht2_max

                lenght_min = self.attr_lenght_min - self.attr_lenght_max
                lenght_max = self.attr_lenght_min + self.attr_lenght_max
                min_height = self.attr_height_min - self.attr_height_max
                max_height = self.attr_height_min + self.attr_height_max

                min_height2 = self.attr_height2_min - self.attr_height2_max
                max_height2 = self.attr_height2_min + self.attr_height2_max
                lenght2_min = self.attr_lenght2_min - self.attr_lenght2_max
                lenght2_max = self.attr_lenght2_min + self.attr_lenght2_max

                gasket_od_min = self.attr_gasket_od_min - self.attr_gasket_od_max
                gasket_od_max = self.attr_gasket_od_min + self.attr_gasket_od_max

                flange_hat_min = self.attr_flange_hat_min - self.attr_flange_hat_min
                flange_hat_max = self.attr_flange_hat_min + self.attr_flange_hat_max

                list_avail = []
                # description
                if self.attr_desc and self.attr_model and self.attr_detail and self.attr_gasket_type:
                    gasket_type = self.env.ref('rvd_product_code.gasket_type')
                    ok = (1, 1, 1, 1)
                    value_fill_list.extend(ok)
                    res_code =  code_obj.search([ 
                        ('description', '=', self.attr_desc),
                        ('product_detail', '=', self.attr_detail),
                        ('product_model', '=', self.attr_model),
                    ])
                    if res_code:
                        for code in res_code:
                            attrs =  att_obj.search([ 
                                ('attribute_alias_id', '=', gasket_type.id),
                                ('rvd_product_attribute_code_id', '=', code.id),
                                ('value', '=', self.attr_gasket_type),
                            ])
                            if attrs:
                                codes_list.append(code.id)
                else:
                    if self.attr_desc:
                        description = self.env.ref('rvd_product_code.description')
                        attrs =  code_obj.search([ 
                            ('description', '=', self.attr_desc.upper()),
                        ])
                        if attrs:
                            for code in attrs:
                                codes_list.append(code.id)
                                value_fill_list.append(1)
                    # model
                    if self.attr_model:
                        product_model = self.env.ref('rvd_product_code.product_model')
                        attrs =  att_obj.search([ 
                            ('attribute_alias_id', '=', product_model.id),
                            ('rvd_product_attribute_code_id', '!=', False),
                            ('value', '=', self.attr_model.upper()),
                        ])
                        if attrs:
                            for code in attrs.rvd_product_attribute_code_id:
                                if code.id not in codes_list:
                                    codes_list.append(code.id)
                                    value_fill_list.append(1)
                    # detail
                    if self.attr_detail:
                        product_detail = self.env.ref('rvd_product_code.product_detail')
                        attrs =  att_obj.search([ 
                            ('attribute_alias_id', '=', product_detail.id),
                            ('rvd_product_attribute_code_id', '!=', False),
                            ('value', '=', self.attr_detail.upper()),
                        ])
                        if attrs:
                            for code in attrs.rvd_product_attribute_code_id:
                                if code.id not in codes_list:
                                    codes_list.append(code.id)
                                    value_fill_list.append(1)
                    # gasket type
                    if self.attr_gasket_type:
                        gasket_type = self.env.ref('rvd_product_code.gasket_type')
                        attrs =  att_obj.search([ 
                            ('attribute_alias_id', '=', gasket_type.id),
                            ('rvd_product_attribute_code_id', '!=', False),
                            ('value', '=', self.attr_gasket_type.upper()),
                        ])
                        if attrs:
                            for code in attrs.rvd_product_attribute_code_id:
                                if code.id not in codes_list:
                                    codes_list.append(code.id)
                                    value_fill_list.append(1)

                for code in codes_list:
                    if self.attr_height_min != 0.0 and min_height:
                        height_id = self.env.ref('rvd_product_code.height')
                        attrs=  self.env['rvd.product.attribute'].search([ 
                            ('attribute_alias_id', '=', height_id.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '>', min_height),
                            ('value_int', '<', max_height),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_height2_min != 0.0 and min_height2:
                        height2_id = self.env.ref('rvd_product_code.height2')
                        attrs=  self.env['rvd.product.attribute'].search([ 
                            ('attribute_alias_id', '=', height2_id.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '>', min_height2),
                            ('value_int', '<', max_height2),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_od_min != 0.0 and min_od:
                        od_id = self.env.ref('rvd_product_code.od')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', od_id.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '>', min_od),
                            ('value_int', '<', max_od),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_id_min != 0.0 and min_id:
                        id_id = self.env.ref('rvd_product_code.id')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', id_id.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '>', min_id),
                            ('value_int', '<', max_id),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_gasket_od_min != 0.0 and gasket_od_min:
                        gasket_od = self.env.ref('rvd_product_code.gasket_od')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', gasket_od.id),
                            ('rvd_product_attribute_code_id', '!=', code),
                            ('value_int', '>', gasket_od_min),
                            ('value_int', '<', gasket_od_max),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_thread_min != 0.0:
                        thread_size = self.env.ref('rvd_product_code.thread_size')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', thread_size.id),
                            ('rvd_product_attribute_code_id', '!=', code),
                            ('value_int', '=', self.attr_thread_min),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_thread_nut_min != 0.0:
                        thread_nut_size = self.env.ref('rvd_product_code.thread_nut_size')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', thread_nut_size.id),
                            ('rvd_product_attribute_code_id', '!=', code),
                            ('value_int', '=', self.attr_thread_nut_min),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_flange_hat_min != 0.0 and flange_hat_min:
                        flange_hat = self.env.ref('rvd_product_code.flange_hat')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', flange_hat.id),
                            ('rvd_product_attribute_code_id', '!=', code),
                            ('value_int', '>', flange_hat_min),
                            ('value_int', '<', flange_hat_max),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_lenght_min != 0.0 and lenght_min:
                        length = self.env.ref('rvd_product_code.length')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', length.id),
                            ('rvd_product_attribute_code_id', '!=', code),
                            ('value_int', '>', lenght_min),
                            ('value_int', '<', lenght_max),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_lenght2_min != 0.0 and lenght2_min:
                        length2 = self.env.ref('rvd_product_code.length2')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', length2.id),
                            ('rvd_product_attribute_code_id', '!=', code),
                            ('value_int', '>', lenght2_min),
                            ('value_int', '<', lenght2_max),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_widht_min != 0.0 and widht_min:
                        width = self.env.ref('rvd_product_code.width')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', width.id),
                            ('rvd_product_attribute_code_id', '!=', code),
                            ('value_int', '>', widht_min),
                            ('value_int', '<', widht_max),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_widht2_min != 0.0 and widht2_min:
                        width2 = self.env.ref('rvd_product_code.width2')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', width2.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '>', widht2_min),
                            ('value_int', '<', widht2_max),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_bowl_thread_size_min != 0.0:
                        bowl_thread = self.env.ref('rvd_product_code.bowl_thread_size')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', bowl_thread.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '=', self.attr_bowl_thread_size_min),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if len(list_avail) >= 1:
                        _logger.info("Check")
                        code_available.append(code)

                with_prio = context.get('default_is_attribute')

                if code_available or codes_list:
                    result = []
                    res_product = []
                    if code_available:
                        for code_id in code_available:
                            code = code_obj.browse(code_id)
                            if self.with_prio:
                                prioty_brands = context.get('prior_brand_ids')
                                for brand_id in prioty_brands:
                                    for product in code.product_tmpl_ids.filtered(lambda x: x.product_brand_id.id == brand_id):
                                        result.append(product.id)

                            else:
                                for product in code.product_tmpl_ids:
                                    result.append(product.id)
                    else:
                        for code_id in codes_list:
                            code = code_obj.browse(code_id)
                            if self.with_prio:
                                prioty_brands = context.get('prior_brand_ids')
                                for brand_id in prioty_brands:
                                    for product in code.product_tmpl_ids.filtered(lambda x: x.product_brand_id.id == brand_id):
                                        result.append(product.id)

                            else:
                                for product in code.product_tmpl_ids:
                                    result.append(product.id)


                    for res_id in result:
                        product = self.env['product.template'].browse(res_id)
                        res_product.append((0, 0, {
                            'product_tmpl_id': product.id,
                            'product_variant_id': product.product_variant_id.id,
                            'ritma_code_id': product.rvd_product_template_code_id.id,
                            'brand_id': product.product_brand_id.id,
                            'price': product.list_price,
                            'description': product.rvd_product_template_code_id.description,
                            'lead_id': context.get('lead_id'),
                        }))

                    wiz = self.env['result.product'].create({
                        'rvd_sku': self.rvd_sku,
                        'is_lead': True,
                        'brand_id': self.brand_id.id,
                        'ritma_code_ids': codes_list,
                        'rvd_attribute_ids': self.rvd_attribute_ids.ids,
                        'rvd_equipment_ids': self.rvd_equipment_id.ids,
                        'rvd_product_sku_ids': res_product,
                    })

                    view = self.env.ref('rvd_sale.view_result_product_form')
                    context.update({
                        'product_list': result,
                        'enquiry_id': self.id,
                        'sku': self.rvd_sku,
                        'attributes': self.rvd_attribute_ids.ids,
                        'equipment': self.rvd_equipment_id.ids,
                        # 'order': self.order_id.id,
                        'sku_result': res_product,
                    })

                    return {
                        'name': _('List Product'),
                        'res_model': 'result.product',
                        'type': 'ir.actions.act_window',
                        'views': [(view.id, 'form')],
                        'res_id': wiz.id,
                        'view_mode': 'form',
                        'target': 'new',
                        'context': context,
                    }
        else:
            return super(CustomerEnquiry, self).search_product()

        # return res


class RelationSales(models.Model):
    _name = 'rvd.relation.sales'

    name = fields.Char("Name")
    sales_person = fields.Many2one('res.users', 'Sales Person')
    sales_admin_ids = fields.Many2many('res.users', 'sales_admin_rel', 'relation_id', string='CSS Relation')

    @api.onchange('sales_person')
    def _onchane_name(self):
        for person in self:
            if person.sales_person:
                person.name = person.sales_person.name
            else:
                person.name = False

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         "Name Already exist"),
    ]


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    parent_id = fields.Many2one('crm.team', string='Parent Department')
    type_sales = fields.Selection(
        [('admin', 'CSS'),
         ('person', 'Sales Person'),
        ], string="Sales", default='admin')
    team_member_sales_ids = fields.Many2many('res.users', string='Team Members Sales', check_company=True, domain=[('share', '=', False)], compute='_get_team_sales')
    child_ids = fields.One2many('crm.team', 'parent_id', 'Child Departments')
    team_member_ids = fields.Many2many('res.users', string='Team Members', check_company=True, domain=[('share', '=', False)], compute='_get_team_member')

    @api.depends('member_ids')
    def _get_team_member(self):
        self.team_member_ids = False
        _logger.info("MEMBER")
        _logger.info(self.user_id.team_member_ids)
        self.team_member_ids = [(6, 0, self.user_id.team_member_ids.ids)]
        return {'domain': {'member_ids': [('id', '=', self.user_id.team_member_ids.ids)]}}

    @api.depends('type_sales')
    def _get_team_sales(self):
        for team in self:
            if team.type_sales == 'admin':
                groups_admin = self.env['res.groups'].search([('name', '=', 'CSS')], limit=1)
                self.team_member_sales_ids = [(6, 0, groups_admin.users.ids)]
            if team.type_sales == 'person':
                groups_admin = self.env['res.groups'].search([('name', '=', 'Sales Person')], limit=1)
                self.team_member_sales_ids = [(6, 0, groups_admin.users.ids)]



class Stage(models.Model):
    _inherit = "crm.stage"

    use_sales_admin = fields.Boolean("Use CSS")
    use_sales_person = fields.Boolean("Use Sales Person", default=True)

