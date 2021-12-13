# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, _
from odoo.exceptions import MissingError
import ast


class FalResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

# Mails
    module_fal_auto_block_email = fields.Boolean(
        'Lock Email Template')
    module_fal_hide_external_message = fields.Boolean(
        'Hide Send Message')
    module_fal_hide_icon_chat = fields.Boolean(
        'Hide Icon Chat')
    module_fal_internal_email = fields.Boolean(
        'Internal Email')
    module_fal_internal_message = fields.Boolean(
        'Internal Message')
    module_fal_mail_debrand = fields.Boolean(
        'Mail Debrand')
    module_fal_mail_font = fields.Boolean(
        'Mail Font')
    module_fal_message_body_in_subtype = fields.Boolean(
        'Add Email Template on Subtype')
    module_fal_activity_timesheet = fields.Boolean(
        'Activity to Timesheet')
    module_fal_mail_cc = fields.Boolean(
        'Email recipients information')

# CLuedoo Best Practice
    module_fal_generic_product = fields.Boolean(
        'Product Data Library for Company Expenses')
    module_fal_product_category_structure = fields.Boolean(
        'Product Category Structure')
    module_fal_product_generic = fields.Boolean(
        'Product extra field & features: in stock, generic, copy behavior')
    module_fal_product_size_detail = fields.Boolean(
        'Product Detailed Specification')
    module_fal_configuration_short_panel = fields.Boolean(
        'Add Short Description Search')
    module_fal_product_reference_by_category = fields.Boolean(
        'Product Template Reference by Product Category')
    module_fal_unique_reference = fields.Boolean(
        'Sequence & Reference Management: Unique & Mandatory Reference')
    module_fal_access_right_editable_tree = fields.Boolean(
        'Editable Access Right')
    module_fal_advanced_searchpanel = fields.Boolean(
        'Advance Search Panel')

# Partner
    module_fal_partner_code = fields.Boolean(
        'Partner Code')
    module_fal_partner_private_address = fields.Boolean(
        'Partner Private Address')
    module_fal_partner_short_name = fields.Boolean(
        'Partner Short Name')
    module_fal_partner_user_creation = fields.Boolean(
        'Partner User Creation')
    module_fal_alias_on_partner = fields.Boolean(
        'Alias on Partner')
    module_fal_report_partner = fields.Boolean(
        'Report by Partner')

# Business Type
    module_fal_business_type = fields.Boolean(
        'Business Unit Management')
    module_fal_business_type_sale_ext = fields.Boolean(
        'Sales by Business Unit')
    module_fal_business_type_crm_ext = fields.Boolean(
        'CRM by Business Unit')
    module_fal_business_type_purchase_ext = fields.Boolean(
        'Purchase by Business Unit')
    module_fal_business_type_invoice_ext = fields.Boolean(
        'Invoice by Business Unit')
    module_fal_inter_business_unit = fields.Boolean(
        'Inter Business Unit')

# Comment
    module_fal_comment_template = fields.Boolean(
        'Comment Template')
    module_fal_sale_line_comment = fields.Boolean(
        'Sale Line Comment')
    module_fal_tax_comment = fields.Boolean(
        'Comment on Invoice according to the Tax')

# Contract Condition
    module_fal_contract_conditions = fields.Boolean(
        'Note Template Engine')
    module_fal_contract_conditions_invoice = fields.Boolean(
        'Note Template for Invoice')
    module_fal_contract_conditions_sale = fields.Boolean(
        'Note template for Sales')
    module_fal_contract_conditions_purchase = fields.Boolean(
        'Note Template for Purchase ')

# Contacts
    module_partner_firstname = fields.Boolean(
        'First Name - Last Name on Partner')
    module_fal_group_by_commercial = fields.Boolean(
        'Child Company Management')
    module_fal_dynamic_qualification = fields.Boolean(
        'Dynamic Qualification')
    module_fal_title_company = fields.Boolean(
        'Company Title')
    module_fal_title_company_fr = fields.Boolean(
        'French Company Title Library')

# Cluedoo Validation Process
    module_validation_process = fields.Boolean(
        'Validation Process')

# Tools
    module_create_and_edit_many2one = fields.Boolean(
        'Create and Edit Many2one Feature')
    module_fal_cron_failure_notification_ext = fields.Boolean(
        'Cron Failure Notification Extension')
    module_kanban_draggable = fields.Boolean(
        'Kanban Drag Drop Control')
    module_report_xml = fields.Boolean(
        'XML Reports')
    module_web_tree_image_tooltip = fields.Boolean(
        'Web Image on List View')
    module_web_widget_x2many_2d_matrix = fields.Boolean(
        '2D matrix for x2many fields')
    module_fal_change_background_company = fields.Boolean(
        'Change Background Company')
    module_fal_easy_reporting = fields.Boolean(
        'Export List Management')
    module_auto_backup = fields.Boolean(
        'Database Auto Backup')
    module_fal_configuration_short_panel = fields.Boolean(
        'Configuration Panel Short Description Search')
    module_fal_calendar_multiple_select = fields.Boolean(
        'Multi Select on Calendar View')
    module_fal_drawing_engine = fields.Boolean(
        'Drawing Engine')

# Term and Conditions
    module_terms_conditions = fields.Boolean(
        'Terms and Conditions')

# Setup
    module_fal_document_relation = fields.Boolean(
        'Attachment Management')
    module_smile_decimal_precision = fields.Boolean(
        'Smile Decimal Precision')
    module_fal_queue_job_variant = fields.Boolean(
        'Job Queue Product')
    run_as_queue_job = fields.Boolean(
        help="Specify if this cron should be ran as a queue job",
    )
    fal_channel_id = fields.Many2one(
        comodel_name="queue.job.channel",
        readonly=False,
        string="Channel",
        # default='_compute_run_as_queue_job',
    )
    module_fal_default_main_engine = fields.Boolean(
        'Default Engine')
# Users
    module_fal_add_message_in_user = fields.Boolean(
        'Add Messaging in User view')

# Products
    module_fal_product_attribute_management = fields.Boolean(
        'Product Attribute Management')
    module_fal_product_attribute_management_in_stock = fields.Boolean(
        'Attribute Management in Stock')

# Multi-Company
    module_fal_intercompany_product_configurator = fields.Boolean(
        'Product Configurator on Intercompany')

# Common Object
    module_fal_analytic_account_ext = fields.Boolean(
        'Analytic Account on Journal Entry Source')
    module_fal_intercompany_analytic_account_ext = fields.Boolean(
        'Analytic Intercompany')
    module_fal_hr_timesheet_analytic_multi_company = fields.Boolean(
        'Hr Timesheet Analytic Multi-Company')

# Mail
    module_fal_activity_meeting = fields.Boolean(
        'Meeting Timesheet From Schedule Activity')

# Integration
    module_fal_zoom_integration = fields.Boolean(
        'Zoom Integration')
    module_fal_mattermost_integration = fields.Boolean(
        'Mattermost Integration')

    def open_module(self):
        context = dict(self._context)
        module = context.get('module_id')
        module_id = False
        try:
            module_id = self.env.ref(module).id
        except ValueError:
            raise MissingError(_('This module does not exist'))

        return {
            'type': 'ir.actions.act_window',
            'name': 'Apps',
            'view_mode': 'form',
            'res_model': 'ir.module.module',
            'res_id': module_id,
            'target': 'current',
        }

    @api.onchange('module_fal_queue_job_variant')
    def _onchange_run_job_queue(self):
        if self.module_fal_queue_job_variant:
            self.run_as_queue_job = True

    # @api.depends("run_as_queue_job")
    # def _compute_run_as_queue_job(self):
    #     for prod in self:
    #         if prod.run_as_queue_job and not prod.fal_channel_id:
    #             prod.fal_channel_id = self.env.ref("queue_job_cron.channel_root_product").id
    #         else:
    #             prod.fal_channel_id = False

    @api.model
    def get_values(self):
        res = super(FalResConfigSettings, self).get_values()
        ctx = dict(self._context)
        ICPSudo = self.env['ir.config_parameter'].sudo()
        run_as_queue_job = ICPSudo.get_param(
            'fal_config_setting.run_as_queue_job')
        channel_id = ICPSudo.get_param(
            'fal_config_setting.fal_channel_id')
        res.update(
            run_as_queue_job=run_as_queue_job,
            fal_channel_id=(ast.literal_eval(channel_id) if channel_id else False),
        )
        ctx.update({'run_as_queue_job': True})
        return res

    def set_values(self):
        res = super(FalResConfigSettings, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        ICPSudo.set_param(
            "fal_config_setting.run_as_queue_job",
            self.run_as_queue_job)
        ICPSudo.set_param(
            "fal_config_setting.fal_channel_id",
            self.fal_channel_id.id)
        return res
