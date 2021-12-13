from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from datetime import datetime
import re
import logging

_logger = logging.getLogger(__name__)


class RvdProductCode(models.Model):
    _name = 'rvd.product.code'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Rivindi Code"

    active = fields.Boolean(default=True, help="The active field allows you to hide the template without removing it.")
    name = fields.Char(string='Code', readonly=True, copy=False, tracking=True, required=True)
    image_1920 = fields.Image("Image", compute="_get_image", readonly=False, tracking=True)
    second_image = fields.Image("Second Image", tracking=True)
    third_image = fields.Image("Third Image", tracking=True)
    description = fields.Char(string="Description", compute="_compute_alias", tracking=True, readonly=False, store=True)
    product_detail = fields.Char(string="Product Detail", compute="_compute_alias", tracking=True, readonly=False, store=True)
    product_model = fields.Char(string="Product Model", compute="_compute_alias", tracking=True, readonly=False, store=True)
    product_remark = fields.Char(string="Product Remarks", compute="_compute_alias", tracking=True, readonly=False, store=True)

    set_numbers = fields.Many2many('rvd.product.code', 'set_number_for_table', 'code_id', 'number_id', string='Set Numbers', tracking=True, store=True)
    housing_for_ids = fields.Many2many('rvd.product.code', 'housing_for_table', 'code_id', 'housing_id', string='Housing For', tracking=True, store=True)
    element_for_ids = fields.Many2many('rvd.product.code', 'element_for_table', 'code_id', 'element_id', string='Element For', tracking=True, store=True)
    # add
    bowl_for_ids = fields.Many2many('rvd.product.code', 'bowl_for_table', 'code_id', 'bowl_id', string='Bowl For', tracking=True, store=True)
    heading_setting_for_ids = fields.Many2many('rvd.product.code', 'heading_setting_for_table', 'code_id', 'heading_id', string='Heading Setting For', tracking=True, store=True)
    replacement_element_for_ids = fields.Many2many('rvd.product.code', 'replacement_element_for_table', 'code_id', 'replacement_id', string='Replacement Element Filter Part Number', tracking=True, store=True)
    inner_secoundary_ids = fields.Many2many('rvd.product.code', 'inner_secoundary_table', 'code_id', 'inner_id', string='Inner/Secondary Keycode', tracking=True, store=True)
    replacement_element = fields.Integer(string='Replacement Element/Set (pcs)', tracking=True, store=True)
    alterneted_keycode_ids = fields.Many2many('rvd.product.code', 'alterneted_keycode_table', 'code_id', 'alterneted_id', string='Alterneted Keycode', tracking=True, store=True)
    outer_primary_keycode_ids = fields.Many2many('rvd.product.code', 'outer_primary_keycode_table', 'code_id', 'outer_id', string='Outer/Primary Keycode', tracking=True, store=True)

    product_tmpl_ids = fields.One2many('product.template', 'rvd_product_template_code_id', string='Products', tracking=True, store=True)
    cross_reference_ids = fields.One2many('product.template', 'rvd_product_cr_code_id', string='Cross References', context={'active_test': False}, tracking=True, store=True)
    product_equipment_ids = fields.One2many('product.equipment', 'rvd_product_equipment_code_id', string='Product Equipment', tracking=True, store=True)
    rvd_product_attributes_ids = fields.One2many('rvd.product.attribute', 'rvd_product_attribute_code_id', string='Attributes', compute="_compute_product_attributes", store=True, tracking=True, readonly=False)

    @api.depends('product_tmpl_ids', 'product_tmpl_ids.image_1920')
    def _get_image(self):
        for code in self:
            if code.product_tmpl_ids:
                code.image_1920 = code.product_tmpl_ids[0].image_1920
            else:
                code.image_1920 = False


    @api.depends('rvd_product_attributes_ids', 'rvd_product_attributes_ids.attribute_alias_id')
    def _compute_alias(self):
        for code in self:
            attributes = {}
            for att in code.rvd_product_attributes_ids.filtered(lambda a: a.attribute_alias_id):
                attributes.update({att.attribute_alias_id.name: att.value})
            code.description = attributes.get('DESCRIPTION')
            code.product_model = attributes.get('PRODUCT MODEL')
            code.product_remark = attributes.get('PRODUCT REMARKS')
            code.product_detail = attributes.get('PRODUCT DETAIL')

    @api.depends('product_tmpl_ids', 'rvd_product_attributes_ids')
    def _compute_product_attributes(self):
        for code in self:
            attr_alias_line = self.env['rvd.product.alias.line']
            for product in code.product_tmpl_ids.sorted(key=lambda r: r.product_brand_id.priority, reverse=True):
                for att in product.rvd_product_attributes_ids:
                    for attribute in code.rvd_product_attributes_ids:
                        if att.attribute_alias_id and att.attribute_alias_id == attribute.attribute_alias_id:
                            attribute.rvd_product_attribute_code_id = False
                        elif not attribute.attribute_alias_id:
                            alias_line = attr_alias_line.search([('name', '=', attribute.name)], limit=1)
                            alias_id = self.env['rvd.product.alias'].search([('alias_line_ids', 'in', alias_line.ids)], limit=1)
                            if alias_id:
                                attribute.write({'attribute_alias_id': alias_id.id})
                    att.rvd_product_attribute_code_id = code.id


    def show_on_web_true(self):
        for code in self:
            for cross in code.cross_reference_ids:
                cross.write({'show_on_website': True})

    def show_on_web_false(self):
        for code in self:
            for cross in code.cross_reference_ids:
                cross.write({'show_on_website': False})

    @api.model
    def update_ritma_code(self):
        self.write({
            'active': False,
            'cross_reference_ids': False
        })
        alias_obj = self.env['rvd.product.alias']
        list_attr = []
        list_attr_alias = []
        for product_tmpl in self.product_tmpl_ids:
            cross_ref = product_tmpl.with_context(active_test=True)._find_rvd_product_code()
            for attr in product_tmpl.rvd_product_attributes_ids:
                if attr.attribute_alias_id.id not in list_attr_alias:
                    list_attr_alias.append(attr.attribute_alias_id.id)
                    query_attrs = """
                        UPDATE rvd_product_attribute SET rvd_product_attribute_code_id=%s WHERE id=%s"""
                    self.env.cr.execute(query_attrs, (cross_ref.id, attr.id))


    def values_message(self, new_id, field, res_id):
        # value message
        user_id = self._context.get('uid')
        users = self.env['res.users'].browse(user_id)
        values = {
            'author_id': users.partner_id.id,
            'email_from': users.name,
            'model': 'rvd.product.code',
            'res_id': res_id,
            'message_type': 'notification',
            'is_internal': True,
        }
        return values

    def write(self, vals):
        # check update record many2many
        # Inner Secoundary
        if vals.get('inner_secoundary_ids'):
            rec = []
            fields = self.env['ir.model.fields'].search([('name', '=', 'inner_secoundary_ids')])
            for old_inner in self.inner_secoundary_ids.ids:
                if old_inner not in vals.get('inner_secoundary_ids')[0][2]:
                    old_value_id = self.env['rvd.product.code'].browse(old_inner)
                    rec.append(old_inner)
                    mess_val = self.values_message(old_inner, 'inner_secoundary_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
            for inner in vals.get('inner_secoundary_ids')[0][2]:
                if inner not in self.inner_secoundary_ids.ids:
                    old_value_id = self.env['rvd.product.code'].browse(inner)
                    rec.append(inner)
                    mess_val = self.values_message(inner, 'inner_secoundary_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Add',
                    })]})
                    self.env['mail.message'].create(mess_val)
        # Outer Secoundary
        if vals.get('outer_primary_keycode_ids'):
            rec = []
            fields = self.env['ir.model.fields'].search([('name', '=', 'outer_primary_keycode_ids')])
            for old_inner in self.outer_primary_keycode_ids.ids:
                if old_inner not in vals.get('outer_primary_keycode_ids')[0][2]:
                    old_value_id = self.env['rvd.product.code'].browse(old_inner)
                    rec.append(old_inner)
                    mess_val = self.values_message(old_inner, 'outer_primary_keycode_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
            for inner in vals.get('outer_primary_keycode_ids')[0][2]:
                if inner not in self.outer_primary_keycode_ids.ids:
                    old_value_id = self.env['rvd.product.code'].browse(inner)
                    rec.append(inner)
                    mess_val = self.values_message(inner, 'outer_primary_keycode_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Add',
                    })]})
                    self.env['mail.message'].create(mess_val)
        # Alterneted Keycode
        if vals.get('alterneted_keycode_ids'):
            rec = []
            fields = self.env['ir.model.fields'].search([('name', '=', 'alterneted_keycode_ids')])
            for old_inner in self.alterneted_keycode_ids.ids:
                if old_inner not in vals.get('alterneted_keycode_ids')[0][2]:
                    old_value_id = self.env['rvd.product.code'].browse(old_inner)
                    rec.append(old_inner)
                    mess_val = self.values_message(old_inner, 'alterneted_keycode_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
            for inner in vals.get('alterneted_keycode_ids')[0][2]:
                if inner not in self.alterneted_keycode_ids.ids:
                    old_value_id = self.env['rvd.product.code'].browse(inner)
                    rec.append(inner)
                    mess_val = self.values_message(inner, 'alterneted_keycode_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Add',
                    })]})
                    self.env['mail.message'].create(mess_val)
        # Replacement Element
        if vals.get('replacement_element_for_ids'):
            rec = []
            fields = self.env['ir.model.fields'].search([('name', '=', 'replacement_element_for_ids')])
            for old_inner in self.replacement_element_for_ids.ids:
                if old_inner not in vals.get('replacement_element_for_ids')[0][2]:
                    old_value_id = self.env['rvd.product.code'].browse(old_inner)
                    rec.append(old_inner)
                    mess_val = self.values_message(old_inner, 'replacement_element_for_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
            for inner in vals.get('replacement_element_for_ids')[0][2]:
                if inner not in self.replacement_element_for_ids.ids:
                    old_value_id = self.env['rvd.product.code'].browse(inner)
                    rec.append(inner)
                    mess_val = self.values_message(inner, 'replacement_element_for_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Add',
                    })]})
                    self.env['mail.message'].create(mess_val)
        # Set Numbers
        if vals.get('set_numbers'):
            rec = []
            fields = self.env['ir.model.fields'].search([('name', '=', 'set_numbers')])
            for old_inner in self.set_numbers.ids:
                if old_inner not in vals.get('set_numbers')[0][2]:
                    old_value_id = self.env['rvd.product.code'].browse(old_inner)
                    rec.append(old_inner)
                    mess_val = self.values_message(old_inner, 'set_numbers', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
            for inner in vals.get('set_numbers')[0][2]:
                if inner not in self.set_numbers.ids:
                    old_value_id = self.env['rvd.product.code'].browse(inner)
                    rec.append(inner)
                    mess_val = self.values_message(inner, 'set_numbers', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Add',
                    })]})
                    self.env['mail.message'].create(mess_val)
        # Housing
        if vals.get('housing_for_ids'):
            rec = []
            fields = self.env['ir.model.fields'].search([('name', '=', 'housing_for_ids')])
            for old_inner in self.housing_for_ids.ids:
                if old_inner not in vals.get('housing_for_ids')[0][2]:
                    old_value_id = self.env['rvd.product.code'].browse(old_inner)
                    rec.append(old_inner)
                    mess_val = self.values_message(old_inner, 'housing_for_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
            for inner in vals.get('housing_for_ids')[0][2]:
                if inner not in self.housing_for_ids.ids:
                    old_value_id = self.env['rvd.product.code'].browse(inner)
                    rec.append(inner)
                    mess_val = self.values_message(inner, 'housing_for_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Add',
                    })]})
                    self.env['mail.message'].create(mess_val)
        # Element
        if vals.get('element_for_ids'):
            rec = []
            fields = self.env['ir.model.fields'].search([('name', '=', 'element_for_ids')])
            for old_inner in self.element_for_ids.ids:
                if old_inner not in vals.get('element_for_ids')[0][2]:
                    old_value_id = self.env['rvd.product.code'].browse(old_inner)
                    rec.append(old_inner)
                    mess_val = self.values_message(old_inner, 'element_for_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
            for inner in vals.get('element_for_ids')[0][2]:
                if inner not in self.element_for_ids.ids:
                    old_value_id = self.env['rvd.product.code'].browse(inner)
                    rec.append(inner)
                    mess_val = self.values_message(inner, 'element_for_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Add',
                    })]})
                    self.env['mail.message'].create(mess_val)
        # Bowl
        if vals.get('bowl_for_ids'):
            rec = []
            fields = self.env['ir.model.fields'].search([('name', '=', 'bowl_for_ids')])
            for old_inner in self.bowl_for_ids.ids:
                if old_inner not in vals.get('bowl_for_ids')[0][2]:
                    old_value_id = self.env['rvd.product.code'].browse(old_inner)
                    rec.append(old_inner)
                    mess_val = self.values_message(old_inner, 'bowl_for_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
            for inner in vals.get('bowl_for_ids')[0][2]:
                if inner not in self.bowl_for_ids.ids:
                    old_value_id = self.env['rvd.product.code'].browse(inner)
                    rec.append(inner)
                    mess_val = self.values_message(inner, 'bowl_for_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Add',
                    })]})
                    self.env['mail.message'].create(mess_val)
        # Heading Setting
        if vals.get('heading_setting_for_ids'):
            rec = []
            fields = self.env['ir.model.fields'].search([('name', '=', 'heading_setting_for_ids')])
            for old_inner in self.heading_setting_for_ids.ids:
                if old_inner not in vals.get('heading_setting_for_ids')[0][2]:
                    old_value_id = self.env['rvd.product.code'].browse(old_inner)
                    rec.append(old_inner)
                    mess_val = self.values_message(old_inner, 'heading_setting_for_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
            for inner in vals.get('heading_setting_for_ids')[0][2]:
                if inner not in self.heading_setting_for_ids.ids:
                    old_value_id = self.env['rvd.product.code'].browse(inner)
                    rec.append(inner)
                    mess_val = self.values_message(inner, 'heading_setting_for_ids', self.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': old_value_id.name,
                        'new_value_char': 'Add',
                    })]})
                    self.env['mail.message'].create(mess_val)

        res = super(RvdProductCode, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('rvd.product.code.seq') or 'New'
        res = super(RvdProductCode, self).create(vals)
        return res


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    rvd_product_template_code_id = fields.Many2one('rvd.product.code', 'Rivindi Product Code (For Template)', tracking=True)
    rvd_product_cr_code_id = fields.Many2one('rvd.product.code', 'Rivindi Product Code (For Cross Reference)', tracking=True)
    rvd_discontinue_status = fields.Selection([
        ('release', 'Release'),
        ('discontinue', 'Discontinue')], string='Discontinue Status', default='release', tracking=True)
    rvd_ban_status = fields.Boolean('Ban Status', default=False, tracking=True)
    rvd_product_status = fields.Selection([
        ('full', 'Full Stock'),
        ('needed', 'Needed Stock'),
        ('ban', 'Stock Status')],
        string='Stock Status', default='full', tracking=True)
    rvd_limit_stock = fields.Integer('Limit Stock', company_dependent=True, tracking=True)
    product_brand_id = fields.Many2one(
        "product.brand", string="Brand", context={'active_test': False}, help="Select a brand for this product", tracking=True
    )
    show_on_website = fields.Boolean("Show On Website", default=True, tracking=True)
    is_not_brand = fields.Boolean("Not Brand", default=False)
    image_on_website = fields.Boolean("Image On Website", tracking=True)
    service_hours_ids = fields.Many2many('rvd.pm.service', string="Service")
    # Tracking Fields
    image_1920 = fields.Image(tracking=True)
    barcode = fields.Char(tracking=True)
    name = fields.Char(tracking=True)
    description = fields.Text(tracking=True)
    description_purchase = fields.Text(tracking=True)
    description_sale = fields.Text(tracking=True)
    type = fields.Selection(default='product', tracking=True)
    categ_id = fields.Many2one(tracking=True)
    currency_id = fields.Many2one(tracking=True)
    cost_currency_id = fields.Many2one(tracking=True)
    price = fields.Float(tracking=True)
    list_price = fields.Float(tracking=True)
    lst_price = fields.Float(tracking=True)
    standard_price = fields.Float(tracking=True)
    volume = fields.Float(tracking=True)
    volume_uom_name = fields.Char(tracking=True)
    weight = fields.Float(tracking=True)
    weight_uom_name = fields.Char(tracking=True)
    sale_ok = fields.Boolean(tracking=True)
    purchase_ok = fields.Boolean(tracking=True)
    delivery_ok = fields.Boolean(string='Delivery',tracking=True)
    pricelist_id = fields.Many2one(tracking=True)
    uom_id = fields.Many2one(tracking=True)
    uom_name = fields.Char(tracking=True)
    uom_po_id = fields.Many2one(tracking=True)
    company_id = fields.Many2one(tracking=True)
    packaging_ids = fields.One2many(tracking=True)
    seller_ids = fields.One2many(tracking=True)
    variant_seller_ids = fields.One2many(tracking=True)
    active = fields.Boolean(tracking=True)
    color = fields.Integer(tracking=True)
    taxes_id = fields.Integer(tracking=True)
    is_product_variant = fields.Boolean(tracking=True)
    attribute_line_ids = fields.One2many(tracking=True)
    valid_product_template_attribute_line_ids = fields.Many2many(tracking=True)
    product_variant_ids = fields.One2many(tracking=True)
    product_variant_id = fields.Many2one(tracking=True)
    product_variant_count = fields.Integer(tracking=True)
    barcode = fields.Char(tracking=True)
    default_code = fields.Char(tracking=True)
    description = fields.Text(tracking=True)
    taxes_id = fields.Many2many(tracking=True)
    supplier_taxes_id = fields.Many2many(tracking=True)
    responsible_id = fields.Many2one(tracking=True)
    property_stock_production = fields.Many2one(tracking=True)
    property_stock_inventory = fields.Many2one(tracking=True)
    tracking = fields.Selection(tracking=True)
    description_picking = fields.Text(tracking=True)
    description_pickingout = fields.Text(tracking=True)
    description_pickingin = fields.Text(tracking=True)
    qty_available = fields.Float(tracking=True)
    virtual_available = fields.Float(tracking=True)
    incoming_qty = fields.Float(tracking=True)
    outgoing_qty = fields.Float(tracking=True)
    location_id = fields.Float(tracking=True)
    warehouse_id = fields.Float(tracking=True)
    route_ids = fields.Many2many(tracking=True)
    property_account_income_id = fields.Many2one(tracking=True)
    property_account_expense_id = fields.Many2one(tracking=True)

    def update_product(self):
        self.ensure_one()
        view = self.env.ref('product.product_template_only_form_view')
        return {
            'name': _('Product'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'views': [(view.id, 'form')],
            'view_mode': 'form',
            'target': 'new',
            'res_id': self.id,
            'context': dict(form_view_initial_mode='edit')}

    def delete_ritma_code(self):
        ctx = dict(self._context)
        ritma_code = self.env['rvd.product.code']
        params = ctx.get('params')

        code_id = self.rvd_product_cr_code_id
        if code_id:
            rec = []
            model = self.env['ir.model'].search([('model', '=', 'rvd.product.code')], limit=1)
            fields = self.env['ir.model.fields'].search([('name', '=', 'cross_reference_ids'), ('model_id', '=', model.id)], limit=1)
            if self.id in code_id.cross_reference_ids.ids:
                rec.append(self.id)
                mess_val = ritma_code.values_message(self.id, 'cross_reference_ids', code_id.id)
                mess_val.update({'tracking_value_ids': [(0, 0, {
                    'field': fields.id,
                    'field_desc': fields.field_description,
                    'old_value_char': self.name + ' Brand: ' + self.product_brand_id.name,
                    'new_value_char': 'Delete',
                })]})
                self.env['mail.message'].create(mess_val)
            self.write({
                'rvd_product_cr_code_id': False,
                'rvd_product_template_code_id': False,
            })
        return

    @api.onchange("rvd_product_status")
    def _onchange_ban_status(self):
        if self.rvd_product_status == 'ban':
            self.rvd_ban_status = True
        else:
            self.rvd_ban_status = False

    def _check_duplicated_sku(self, vals=False):
        # check duplicate cross if have used in any ritma code
        ctx = dict(self._context)
        if not ctx.get('automated'):
            if self.name and self.product_brand_id:
                processed_name = re.sub(r'[^\w]', '', self.name).upper()
                product_find = self.env['product.template'].search([
                    '|', ('name', '=', processed_name), ('processed_name', '=', processed_name),
                    ('product_brand_id', '=', self.product_brand_id.id)], limit=1)
                product_find_archive = self.env['product.template'].search([
                    '|', ('name', '=', processed_name), ('processed_name', '=', processed_name),
                    ('product_brand_id', '=', self.product_brand_id.id),
                    ('active', '=', False)], limit=1)

                if product_find or product_find_archive:
                    raise ValidationError(_('Product : "%s", with Brand :"%s" already exist in Ritma Code : %s.' % (self.name, self.product_brand_id.name.strip(), product_find.rvd_product_cr_code_id.name or product_find_archive.rvd_product_cr_code_id.name)))

    def add_image(self):
        ctx = dict(self._context)
        ritma_code = self.env['rvd.product.code']
        if not ctx.get('automated'):
            code = self.rvd_product_template_code_id
            if code:
                if not code.image_1920:
                    code.write({'image_1920': self.image_1920})
                elif not code.second_image:
                    code.write({'second_image': self.image_1920})
                elif not code.third_image:
                    code.write({'third_image': self.image_1920})
            

    @api.onchange('name', 'product_brand_id')
    def _onchange_sku(self):
        self._check_duplicated_sku()
        # if self.name and self.product_brand_id:
        #     warning_mess = {
        #         'title': _('Record Change.'),
        #         'message': _('You sure change this record.')
        #     }
        #     return {'warning': warning_mess}

    @api.depends("name")
    # Processed Name is a Char field that is similar to Name, but without special character
    def _get_processed_name(self):
        for product_template in self:
            name = product_template.name
            if "SAKURA FILTER " in product_template.name:
                name = product_template.name.replace('SAKURA FILTER ', '')
            product_template.processed_name = re.sub(r'[^\w]', '', name).upper()
        # for product_template in self:
        #     name = product_template.name
        #     if name:
        #         if "SAKURA FILTER " in product_template.name:
        #             name = product_template.name.replace('SAKURA FILTER ', '')
        #         product_template.processed_name = re.sub(r'[^\w]', '', name).upper()
        #     else:
        #         product_template.processed_name = False

    processed_name = fields.Char("Processed Name", compute="_get_processed_name", store=True)

    def write(self, vals):
        # self._check_duplicated_sku(vals)
        ritma_code = self.env['rvd.product.code']
        ctx = dict(self._context)
        params = ctx.get('params')
        if not ctx.get('automated') and ctx.get('active_test'):
            if vals.get('rvd_product_template_code_id'):
                self.write({
                    'rvd_product_cr_code_id': vals.get('rvd_product_template_code_id')})

        # create tracking if active model in ritma code
        if params:
            if params.get('model') == 'rvd.product.code':
                model = self.env['ir.model'].search([('model', '=', 'product.template')], limit=1)
                if vals.get('name') and vals.get('product_brand_id') or vals.get('product_brand_id'):
                    brand_id = self.env['product.brand'].browse(vals.get('product_brand_id')) or self.product_brand_id
                    fields = self.env['ir.model.fields'].search([('name', '=', 'name'), ('model_id', '=', model.id)], limit=1)
                    mess_val = False
                    # create tracking on ritma code
                    if vals.get('name'):
                        mess_val = ritma_code.values_message(self.id, 'name', self.rvd_product_cr_code_id.id)
                        mess_val.update({'tracking_value_ids': [(0, 0, {
                            'field': fields.id,
                            'field_desc': 'Cross Number',
                            'old_value_char': self.name + ' Brand : ' + self.product_brand_id.name,
                            'new_value_char': vals.get('name') + ' Brand : ' + brand_id.name,
                        })]})
                    if vals.get('product_brand_id'):
                        name = vals.get('name') or self.name
                        mess_val = ritma_code.values_message(self.id, 'product_brand_id', self.rvd_product_cr_code_id.id)
                        mess_val.update({'tracking_value_ids': [(0, 0, {
                            'field': fields.id,
                            'field_desc': 'Cross Number',
                            'old_value_char': self.name + ' Brand : ' + self.product_brand_id.name,
                            'new_value_char': name + ' Brand : ' + brand_id.name,
                        })]})
                    self.env['mail.message'].create(mess_val)
        res = super(ProductTemplate, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        templates = super(ProductTemplate, self).create(vals)
        # templates._find_rvd_product_code()
        ctx = dict(self._context)

        params = ctx.get('params')
        ritma_obj = self.env['rvd.product.code']
        if params and ctx.get('active_test') == False:
            mess_val = False
            if params.get('model') == 'rvd.product.code':
                # set value
                model = self.env['ir.model'].search([('model', '=', 'rvd.product.code')], limit=1)
                fields = self.env['ir.model.fields'].search([('name', '=', 'cross_reference_ids'), ('model_id', '=', model.id)], limit=1)
                name = vals.get('name')
                code_id = vals.get('rvd_product_cr_code_id')
                brand_id = self.env['product.brand'].browse(vals.get('product_brand_id'))
                # create tracking message
                mess_val = ritma_obj.values_message(self.id, 'product_brand_id', code_id)
                mess_val.update({'tracking_value_ids': [(0, 0, {
                    'field': fields.id,
                    'field_desc': 'Cross Ref ',
                    'old_value_char': name + ' Brand : ' + brand_id.name,
                    'new_value_char': "Add",
                })]})
            self.env['mail.message'].create(mess_val)
        return templates

    @api.model
    def update_ritma_code_in_product(self):
        list_attr = []
        list_attr_alias = []
        for product_tmpl in self.filtered(lambda x: x.active):
            cross_ref = product_tmpl.with_context(automated=True)._find_rvd_product_code()
            for attr in product_tmpl.rvd_product_attributes_ids:
                if attr.attribute_alias_id.id not in list_attr_alias:
                    list_attr_alias.append(attr.attribute_alias_id.id)
                    query_attrs = """
                        UPDATE rvd_product_attribute SET rvd_product_attribute_code_id=%s WHERE id=%s"""
                    self.env.cr.execute(query_attrs, (cross_ref.id, attr.id))

    # Try to find Rvd Product Code that has any similarities with current template cross-reference
    def _find_rvd_product_code(self):
        attr_alias_line = self.env['rvd.product.alias.line']
        list_alias = []
        for product_template in self.filtered(lambda x: x.active):
            print('PRODUCT TEMPLATE', product_template.name)
            rvd_code_obj = self.env['rvd.product.code']
            ctx = dict(self._context)

            products_name = [product_template.processed_name]
            brand_ids = [product_template.product_brand_id.id]
            list_attr_alias = []
            if product_template.cross_reference_ids:
                for cross in product_template.cross_reference_ids:
                    products_name.append(cross.processed_name)
                    brand_ids.append(cross.product_brand_id.id)

            # if product_template.rvd_product_attributes_ids:
            #     for attribute in product_template.rvd_product_attributes_ids.filtered(lambda x: x.attribute_alias_id):
            #         list_attr_alias.append(attribute.id)

            # Check name and brand on Rivindi Code
            cross_ref = rvd_code_obj.with_context(active_test=False).search([('cross_reference_ids.processed_name', 'in', products_name), ('cross_reference_ids.product_brand_id', 'in', brand_ids)], limit=1)

            if not cross_ref:
                # cross_ref = rvd_code_obj.create({'rvd_product_attributes_ids': [(6, 0, product_template.rvd_product_attributes_ids.ids)]})
                cross_ref = rvd_code_obj.create({})

            # if cross_ref.id != product_template.id:
            # product_template.write({'rvd_product_template_code_id': cross_ref.id})
            # product_template.write({'rvd_product_cr_code_id': cross_ref.id})
            query_prod = """
                UPDATE product_template SET rvd_product_template_code_id=%s, rvd_product_cr_code_id=%s WHERE id=%s"""
            self.env.cr.execute(query_prod, (cross_ref.id, cross_ref.id, product_template.id))

            # Add code to reference with query
            for cross_product in product_template.cross_reference_ids:
                query_cross = """
                    UPDATE product_template SET rvd_product_cr_code_id=%s WHERE id=%s"""
                self.env.cr.execute(query_cross, (cross_ref.id, cross_product.id))

            # attributes
            for attribute in product_template.rvd_product_attributes_ids:
                if attribute.attribute_alias_id:
                    list_alias.append(attribute.id)
                elif not attribute.attribute_alias_id:
                    query_attrs = """
                        UPDATE rvd_product_attribute SET rvd_product_attribute_code_id=%s WHERE id=%s"""
                    self.env.cr.execute(query_attrs, (cross_ref.id, attribute.id))
            # Add code to equipment
            if ctx.get('active_test'):
                # product_template.product_equipment_ids.with_context(automated=True).write({'rvd_product_equipment_code_id': cross_ref.id})
                for equipment in product_template.product_equipment_ids:
                    query_cross = """
                        UPDATE product_equipment SET rvd_product_equipment_code_id=%s WHERE id=%s"""
                    self.env.cr.execute(query_cross, (cross_ref.id, equipment.id))
            else:
                # product_template.product_equipment_ids.write({'rvd_product_equipment_code_id': cross_ref.id})
                for equipment in product_template.product_equipment_ids:
                    query_cross = """
                        UPDATE product_equipment SET rvd_product_equipment_code_id=%s WHERE id=%s"""
                    self.env.cr.execute(query_cross, (cross_ref.id, equipment.id))

            return cross_ref


            # # 1. Fastest way is to loop for each cross-ref, process the name and make a search for that name.
            # similar_ids = self.with_context(active_test=False).search([('processed_name', '=', product_template.processed_name)])
            # # 2. If Found, means just need to put the template to the Rvd Product Code
            # if any(similar_id.rvd_product_template_code_id or similar_id.rvd_product_cr_code_id for similar_id in similar_ids):
            #     similar_id = similar_ids[0]
            #     product_template.rvd_product_cr_code_id = similar_id.rvd_product_cr_code_id.id
            #     if product_template.active:
            #         product_template.rvd_product_template_code_id = similar_id.rvd_product_template_code_id.id
            #     else:
            #         product_template.rvd_product_cr_code_id = similar_id.rvd_product_cr_code_id.id
            # # 3. If not found, create a new Rvd Code
            # else:
            #     name = self.env['ir.sequence'].next_by_code('rvd.product.code.seq') or 'New'
            #     rvd_id = self.env['rvd.product.code'].create({'name': name})
            #     # 4. Put the new created Rivindi Product Code on the Product Templates
            #     similar_ids.filtered(lambda x: not x.active).write({'rvd_product_cr_code_id': rvd_id.id})
            #     similar_ids.filtered(lambda x: x.active).write({'rvd_product_template_code_id': rvd_id.id})


class ProductEquipment(models.Model):
    _inherit = 'product.equipment'

    rvd_product_equipment_code_id = fields.Many2one('rvd.product.code', 'Rivindi Product Code (For Equipment)')
    service_hours = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6')],
        string='Service Hours', default='1')

    def delete_ritma_code(self):
        ctx = dict(self._context)
        ritma_code = self.env['rvd.product.code']
        params = ctx.get('params')

        code_id = self.rvd_product_equipment_code_id
        if code_id:
            rec = []
            model = self.env['ir.model'].search([('model', '=', 'rvd.product.code')], limit=1)
            fields = self.env['ir.model.fields'].search([('name', '=', 'product_equipment_ids'), ('model_id', '=', model.id)], limit=1)
            if self.id in code_id.product_equipment_ids.ids:
                rec.append(self.id)
                mess_val = ritma_code.values_message(self.id, 'product_equipment_ids', code_id.id)
                mess_val.update({'tracking_value_ids': [(0, 0, {
                    'field': fields.id,
                    'field_desc': fields.field_description,
                    'old_value_char': self.name,
                    'new_value_char': 'Delete',
                })]})
                self.env['mail.message'].create(mess_val)
            self.write({
                'rvd_product_equipment_code_id': False,
            })
        return

    def _check_duplicated_equipment(self):
        ctx = dict(self._context)
        if not ctx.get('automated'):
            for equip in self.rvd_product_equipment_code_id.product_equipment_ids.filtered(lambda a: a._origin.id != self._origin.id):
                if self.name == equip.name and self.year == equip.year \
                        and self.equipment_type == equip.equipment_type \
                        and self.equipment_options == equip.equipment_options \
                        and self.engine == equip.engine \
                        and self.engine_options == equip.engine_options \
                        and self.fuel == equip.fuel \
                        and self.cc == equip.cc \
                        and self.kw == equip.kw:
                    raise UserError(_('Equipment is already exist'))

    @api.onchange('name', 'year', 'equipment_type', 'equipment_options', 'engine', 'engine_options', 'fuel', 'cc', 'kw')
    def _onchange_equipment(self):
        self._check_duplicated_equipment()

    @api.model
    def create(self, vals):
        res = super(ProductEquipment, self).create(vals)
        ctx = dict(self._context)
        ritma_obj = self.env['rvd.product.code']
        if not ctx.get('automated'):
            self._check_duplicated_equipment()
            params = ctx.get('params')
            if params:
                mess_val = False
                if params.get('model') == 'rvd.product.code':
                    # set value
                    model = self.env['ir.model'].search([('model', '=', 'rvd.product.code')], limit=1)
                    fields = self.env['ir.model.fields'].search([('name', '=', 'product_equipment_ids'), ('model_id', '=', model.id)], limit=1)
                    name = vals.get('name')
                    code_id = vals.get('rvd_product_equipment_code_id')
                    # create tracking message
                    mess_val = ritma_obj.values_message(self.id, 'name', code_id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': 'Equipment ',
                        'old_value_char': name,
                        'new_value_char': "Add",
                    })]})
                self.env['mail.message'].create(mess_val)
        return res

    def write(self, vals):
        res = super(ProductEquipment, self).write(vals)
        ctx = dict(self._context)
        if not ctx.get('automated'):
            for item in self:
                item._check_duplicated_equipment()
        return res

    def unlink(self):
        ctx = dict(self._context)
        ritma_code = self.env['rvd.product.code']
        params = ctx.get('params')
        if params:
            code_id = ritma_code.browse(params.get('id'))
            rec = []
            if params.get('model') == 'rvd.product.code':
                model = self.env['ir.model'].search([('model', '=', 'rvd.product.code')], limit=1)
                fields = self.env['ir.model.fields'].search([('name', '=', 'product_equipment_ids'), ('model_id', '=', model.id)], limit=1)
                if self.id in code_id.product_equipment_ids.ids:
                    rec.append(self.id)
                    mess_val = ritma_code.values_message(self.id, 'product_equipment_ids', code_id.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': self.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
        return super(ProductEquipment, self).unlink()


class RvdProductAttributes(models.Model):
    _inherit = 'rvd.product.attribute'

    rvd_product_attribute_code_id = fields.Many2one('rvd.product.code', 'Rivindi Product Code (For Attribute)')
    attribute_alias_id = fields.Many2one('rvd.product.alias', string="Alias", compute="_compute_get_attribute_alias", store=True)

    def delete_ritma_code(self):
        ctx = dict(self._context)
        ritma_code = self.env['rvd.product.code']
        params = ctx.get('params')

        code_id = self.rvd_product_attribute_code_id
        if code_id:
            rec = []
            model = self.env['ir.model'].search([('model', '=', 'rvd.product.code')], limit=1)
            fields = self.env['ir.model.fields'].search([('name', '=', 'rvd_product_attributes_ids'), ('model_id', '=', model.id)], limit=1)
            if self.id in code_id.rvd_product_attributes_ids.ids:
                rec.append(self.id)
                mess_val = ritma_code.values_message(self.id, 'rvd_product_attributes_ids', code_id.id)
                mess_val.update({'tracking_value_ids': [(0, 0, {
                    'field': fields.id,
                    'field_desc': fields.field_description,
                    'old_value_char': self.name + ' Values : ' + self.value,
                    'new_value_char': 'Delete',
                })]})
                self.env['mail.message'].create(mess_val)

            self.write({
                'rvd_product_attribute_code_id': False,
            })

    def _compute_get_attribute_alias(self):
        for att in self:
            alias_line = self.env['rvd.product.alias.line'].search([('name', '=', att.name), ('product_alias_id', '!=', False)], limit=1)
            att.attribute_alias_id = alias_line.product_alias_id.id

    def create(self, vals):
        res = super(RvdProductAttributes, self).create(vals)
        ctx = dict(self._context)
        ritma_obj = self.env['rvd.product.code']
        if not ctx.get('automated'):
            for val in vals:
                if val['product_tmpl_id']:
                    product_template = self.env['product.template'].browse(val['product_tmpl_id'])
                    res['rvd_product_attribute_code_id'] = product_template.rvd_product_template_code_id
                elif not val['product_tmpl_id']:
                    pass

                params = ctx.get('params')
                if params:
                    mess_val = False
                    if params.get('model') == 'rvd.product.code':
                        # set value
                        model = self.env['ir.model'].search([('model', '=', 'rvd.product.code')], limit=1)
                        fields = self.env['ir.model.fields'].search([('name', '=', 'rvd_product_attributes_ids'), ('model_id', '=', model.id)], limit=1)
                        name = val.get('name')
                        code_id = val.get('rvd_product_attribute_code_id')
                        # create tracking message
                        mess_val = ritma_obj.values_message(self.id, 'name', code_id)
                        mess_val.update({'tracking_value_ids': [(0, 0, {
                            'field': fields.id,
                            'field_desc': 'Equipment ',
                            'old_value_char': name,
                            'new_value_char': "Add",
                        })]})
                    self.env['mail.message'].create(mess_val)
        return res

    def unlink(self):
        ctx = dict(self._context)
        ritma_code = self.env['rvd.product.code']
        params = ctx.get('params')
        if params:
            code_id = ritma_code.browse(params.get('id'))
            rec = []
            if params.get('model') == 'rvd.product.code':
                model = self.env['ir.model'].search([('model', '=', 'rvd.product.code')], limit=1)
                fields = self.env['ir.model.fields'].search([('name', '=', 'rvd_product_attributes_ids'), ('model_id', '=', model.id)], limit=1)
                if self.id in code_id.rvd_product_attributes_ids.ids:
                    rec.append(self.id)
                    mess_val = ritma_code.values_message(self.id, 'rvd_product_attributes_ids', code_id.id)
                    mess_val.update({'tracking_value_ids': [(0, 0, {
                        'field': fields.id,
                        'field_desc': fields.field_description,
                        'old_value_char': self.name,
                        'new_value_char': 'Delete',
                    })]})
                    self.env['mail.message'].create(mess_val)
        return super(RvdProductAttributes, self).unlink()


class ProductAlias(models.Model):
    _name = 'rvd.product.alias'

    name = fields.Char(string="Name", required=True)
    alias_line_ids = fields.One2many('rvd.product.alias.line', 'product_alias_id', string="Alias")


class PmService(models.Model):
    _name = 'rvd.pm.service'

    name = fields.Char(string="Name")


class ProductAliasLine(models.Model):
    _name = 'rvd.product.alias.line'

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    product_alias_id = fields.Many2one('rvd.product.alias', string="Product Alias", ondelete='cascade')


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        product_ids = super(ProductProduct, self)._name_search(name, args, operator, limit, name_get_uid)
        if name:
            cross_references = list(self._search(args + [('processed_name', operator, name), ('id', 'not in', product_ids)], limit=limit, access_rights_uid=name_get_uid))
            if cross_references:
                product_ids.extend(cross_references)
        return product_ids
