# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang, get_lang
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    enquiry_ids = fields.One2many('customer.enquiry.line', 'order_id', string='Customer Enquiry', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=False)
    temporary_ids = fields.One2many('temporary.order', 'order_id', string='Temporary Order', copy=False)
    prior_brand_ids = fields.Many2many('product.brand', string="Merk Prioritas")
    po_file = fields.Binary('File PO')
    po_second_file = fields.Binary('File PO 2')
    file_po_file_name = fields.Char('File PO Name')
    file_po_second_file_name = fields.Char('File PO Name')

    # compute quota pricelist
    def _action_confirm(self):
        if not self.po_file and not self.po_second_file:
            raise ValidationError(_("Please input PO File"))
        # for order in self:
        if self.pricelist_id:
            for line in self.order_line:
                items = self.pricelist_id._compute_price_rule_get_items([(line.product_id, line.product_uom_qty, self.partner_id)], self.date_order, line.product_uom_qty, line.product_id.product_tmpl_id.ids, line.product_id.ids, line.product_id.categ_id.ids)
                for item in items.filtered(lambda x: x.is_quota):
                    if item:
                        if item.applied_on == '0_product_variant' and item.product_id == line.product_id:
                            if item.use_quota > line.product_uom_qty:
                                qty = item.use_quota
                                item.write({'use_quota': qty - line.product_uom_qty})
                                continue
                            else:
                                line.write({
                                    'harga_satuan': line.product_id.lst_price,
                                    'price_unit': line.product_id.lst_price,
                                })
                                # raise ValidationError("Exceeds the limits quota")
                        elif item.applied_on == '1_product' and item.product_tmpl_id == line.product_id.product_tmpl_id:
                            if item.use_quota > line.product_uom_qty:
                                qty = item.use_quota
                                item.write({'use_quota': qty - line.product_uom_qty})
                                continue
                            else:
                                # line.onchange_warning()
                                line.write({
                                    'harga_satuan': line.product_id.lst_price,
                                    'price_unit': line.product_id.lst_price,
                                })
                                # return res
                                # raise ValidationError("Exceeds the limits quota")
                        elif item.applied_on == '4_brand' and item.product_brand_id == line.product_id.product_brand_id:
                            if item.use_quota > line.product_uom_qty:
                                qty = item.use_quota
                                item.write({'use_quota': qty - line.product_uom_qty})
                                continue
                            else:
                                line.write({
                                    'harga_satuan': line.product_id.lst_price,
                                    'price_unit': line.product_id.lst_price,
                                })
                                # raise ValidationError("Exceeds the limits quota")
                        elif item.applied_on == '2_product_category':
                            cat = line.product_id.categ_id
                            while cat:
                                if cat.id == price_item.categ_id.id:
                                    break
                                if item.use_quota > line.product_uom_qty:
                                    qty = item.use_quota
                                    item.write({'use_quota': qty - line.product_uom_qty})
                                    continue
                                else:
                                    line.write({
                                        'harga_satuan': line.product_id.lst_price,
                                        'price_unit': line.product_id.lst_price,
                                    })
                                    # raise ValidationError("Exceeds the limits quota")
                        elif item.applied_on == '3_global':
                            if item.use_quota > line.product_uom_qty:
                                qty = item.use_quota
                                item.write({'use_quota': qty - line.product_uom_qty})
                                continue
                            else:
                                line.write({
                                    'harga_satuan': line.product_id.lst_price,
                                    'price_unit': line.product_id.lst_price,
                                })
                                # raise ValidationError("Exceeds the limits quota")
        return super(SaleOrder, self)._action_confirm()

    @api.onchange('user_id', 'partner_id')
    def onchange_user_id(self):
        super().onchange_user_id()
        if self.state in ['draft','sent']:
            if self.partner_id.warehouse_id:
                self.warehouse_id = self.partner_id.warehouse_id
            else:
                self.warehouse_id = self.user_id.with_company(self.company_id.id)._get_default_warehouse_id().id

    def update_prices(self):
        self.ensure_one()
        lines_to_update = []
        for line in self.order_line.filtered(lambda line: not line.display_type):
            product = line.product_id.with_context(
                partner=self.partner_id,
                quantity=line.product_uom_qty,
                date=self.date_order,
                pricelist=self.pricelist_id.id,
                uom=line.product_uom.id
            )
            price_unit = self.env['account.tax']._fix_tax_included_price_company(
                line._get_display_price(product), line.product_id.taxes_id, line.tax_id, line.company_id)
            if self.pricelist_id.discount_policy == 'without_discount' and price_unit:
                discount = max(0, (price_unit - product.price) * 100 / price_unit)
            else:
                discount = 0
            lines_to_update.append((1, line.id, {'price_unit': price_unit, 'harga_satuan': price_unit, 'discount': discount}))
        self.update({'order_line': lines_to_update})
        self.show_update_pricelist = False
        self.message_post(body=_("Product prices have been recomputed according to pricelist <b>%s<b> ", self.pricelist_id.display_name))

    @api.onchange('partner_id', 'partner_id.prior_brand_ids')
    def onchange_prio_brand(self):
        if self.partner_id.prior_brand_ids:
            self.prior_brand_ids = self.partner_id.prior_brand_ids
        else:
            self.prior_brand_ids = False

    def search_by_attr(self):
        context = dict(self.env.context)
        context.update({'is_attribute': True, 'prior_brand_ids': self.prior_brand_ids.ids, 'with_prio': True})
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

    def add_to_order_line(self):
        # Add Enquiry Equipment to Sale Order Line
        result = []
        for enquiry in self.enquiry_ids:
            products = self.env['product.product'].search([('processed_name', 'like', enquiry.rvd_sku)])
            if products:
                for product in products:
                    result.append({
                        'order_id': self.id,
                        'product_id': product.id,
                        'product_template_id': product.product_tmpl_id.id,
                        'name': product.name,
                        'product_uom_qty': enquiry.quantity,
                    })
                enquiry.write({
                    'product_id': product.id,
                    'name': product.name,
                })
            else:
                enquiry.write({
                    'remarks': "Not Found",
                })
        self.env['sale.order.line'].create(result)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """  Override  """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return

        self = self.with_company(self.company_id)

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.sales_admin_id or self.partner_id.commercial_partner_id.sales_admin_id
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.context.get('default_user_id', self.env.uid)
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id


        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            values['team_id'] = self.env['crm.team'].with_context(
                default_team_id=self.partner_id.team_id.id
            )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)], user_id=user_id)

        self.update(values)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('route_id')
    def _compute_route_warehouse(self):
        for line in self:
            temp = []
            location_list = []
            route_wh_obj = self.env['route.warehouse']
            routes = route_wh_obj.search([('order_line_id', '=', self.id)])
            gap_qty = line.product_uom_qty

            if line.route_id:
                location_current = line.warehouse_id.lot_stock_id
                onhand_current = line.product_id.product_tmpl_id.with_context(location=location_current.id).qty_available
                gap_qty = gap_qty - onhand_current
                for rule in line.route_id.rule_ids.filtered(lambda x: x.location_src_id.usage == 'internal' and x.location_src_id.id != location_current.id):
                    location_list.append(rule.location_src_id.id)
                    if not routes:
                        onhand = line.product_id.product_tmpl_id.with_context(location=rule.location_src_id.id).qty_available
                        _logger.info(onhand)
                        if gap_qty > onhand_current:
                            if gap_qty and gap_qty > onhand:
                                temp.append(line._prepare_values_check_stock(rule.location_src_id, rule.warehouse_id, onhand, line.product_id, line.total_volume, line.total_weight, line))
                                gap_qty = gap_qty - onhand
                                route_wh_obj.create(temp)
                            else:
                                temp.append(line._prepare_values_check_stock(rule.location_src_id, rule.warehouse_id, gap_qty, line.product_id, line.total_volume, line.total_weight, line))
                                gap_qty = 0
                                route_wh_obj.create(temp)
                    else:
                        list_wh = []
                        for route in routes:
                            if route.from_wh_id.id not in list_wh:
                                list_wh.append(route.from_wh_id.id)
                                line.route_warehouse_ids += route

    @api.depends('harga_pengajuan', 'harga_satuan')
    def _compute_percentage(self):
        for line in self:
            percent = 0.0
            if line.harga_satuan and line.harga_pengajuan:
                percent = ((line.harga_satuan - line.harga_pengajuan) / line.harga_satuan) * 100
            line.percentage = percent


    done_add_ship = fields.Boolean("Add Shipping")
    rvd_merk = fields.Char('Merk')
    rvd_kode_customer = fields.Char('Kode Customer')
    percentage = fields.Float('Percentage', compute='_compute_percentage', store=True, readonly=False)
    harga_satuan = fields.Float('Harga Satuan')
    harga_pengajuan = fields.Float('Harga Pengajuan')
    harga_markup = fields.Float('Harga Markup')
    harga_non_stock = fields.Float('Harga Non Stock')
    total_shipping = fields.Float('Total Shipping')
    remarks = fields.Char('Remarks')
    ket_stock = fields.Char('Keterangan Stock')
    reason = fields.Char('Reason')
    from_wh_id = fields.Many2one('stock.warehouse', string="From WH")
    total_weight = fields.Float("Total Weight", compute='_compute_weigt_volume')
    total_volume = fields.Float("Total Volume", compute='_compute_weigt_volume')
    route_id = fields.Many2one('stock.location.route', string='Route', domain="[('percepatan_select', '=', True), ('sale_selectable', '=', True), ('warehouse_ids', '=', warehouse_id)]", ondelete='restrict', check_company=True)
    route_warehouse_ids = fields.Many2many('route.warehouse', 'order_line_id', compute='_compute_route_warehouse', string="Route Warehouse", readonly=False)
    choose_product_id = fields.Many2one('choose.product.select', string="Choose Product")
    # so_line_ids = fields.Many2many('sale.order.line', string="So Line")


    @api.depends('product_id')
    def _compute_weigt_volume(self):
        for line in self:
            line.total_weight = line.product_id.weight
            line.total_volume = line.product_id.volume

    def action_open_product_select(self):
        _logger.info("SSSSSSSSSS")
        view_id = self.env.ref('rvd_sale.choose_product_select_form_simple').id
        return {
            'name': 'Choose Product',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'choose.product.select',
            # 'res_id': self.id,
            'views': [(view_id, 'form')],
            'target': 'new',
        }

    def action_open_internal_shipping(self):
        view_id = self.env.ref('rvd_sale.view_sale_orderline_check_route').id
        return {
            'name': 'Internal Route',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.order.line',
            'res_id': self.id,
            'views': [(view_id, 'form')],
            'target': 'new',
            'context': {
                'default_order_line_id': self.id,
                'routes': self.route_warehouse_ids.ids,
            }
        }

    @api.model
    def get_choose_product(self, res_id):
        choose_product = False
        so = self.env['sale.order.line'].browse(res_id)
        if so.choose_product_id:
            choose_product = so.choose_product_id.id
        return choose_product

    def _prepare_values_check_stock(self, location, warehouse, onhand, product, total_volume, total_weight, line):
        return {
            'from_wh_id': location.id,
            'quantity': onhand,
            'total_volume': total_volume,
            'total_weight': total_weight,
            'order_line_id': line.id,
        }

    @api.onchange('route_id')
    def route_id_change(self):
        if not self.route_id and self.product_id and self.order_id.pricelist_id:
            self.done_add_ship = False
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.harga_satuan = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)


    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        product = self.product_id.with_context(
            lang=get_lang(self.env, self.order_id.partner_id.lang).code,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        vals.update(rvd_merk=self.get_brand_name(product))

        if self.order_id.partner_id and self.order_id.pricelist_id:
            vals['harga_satuan'] = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

        self.update(vals)
        return res

    @api.onchange('product_id.lst_price')
    def onchange_warning(self):
        warning_mess = {
            'title': _('Target Duration is inconsistent.'),
            'message': _('Please check with meeting details.')
        }
        return {'warning': warning_mess}


    @api.onchange('harga_pengajuan', 'harga_markup', 'harga_non_stock', 'harga_satuan')
    def onchange_price_unit(self):
        if self.harga_pengajuan:
            self.price_unit = self.harga_pengajuan
        if self.harga_markup:
            self.price_unit = self.harga_markup
        if self.harga_non_stock:
            self.price_unit = self.harga_non_stock
        # if self.harga_satuan:
        #     self.price_unit = self.harga_satuan

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.harga_satuan = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)
            if not self.harga_markup and not self.harga_non_stock and not self.harga_pengajuan:
                self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)

    @api.constrains('harga_markup', 'harga_pengajuan')
    def _check_harga_markup(self):
        for line in self:
            if line.harga_markup > 0.0:
                if line.harga_markup < line.harga_pengajuan:
                    raise ValidationError("Maaf, Harga Negosiator lebih rendah dari pengajuan")

    def get_brand_name(self, product):
        if product.product_brand_id:
            name = product.product_brand_id.name
            return name
        else:
            return False

    # override
    def get_sale_order_line_multiline_description_sale(self, product):
        """ Compute a default multiline description for this sales order line."""
        if product.rvd_product_template_code_id:
            name = product.rvd_product_template_code_id.description
            return name
        else:
            return product.get_product_multiline_description_sale() + self._get_sale_order_line_multiline_description_variants()

    def set_value_harga(self):
        res_total = 0.0
        for route in self.route_warehouse_ids:
            res_total += route.price_unit
        res_tot_satuan = res_total / self.product_uom_qty
        if not self.done_add_ship:
            self.write({
                'done_add_ship': True,
                'total_shipping': res_total,
                'harga_satuan': self.harga_satuan + res_tot_satuan,
                'price_unit': self.price_unit + res_tot_satuan,
            })
        return


class TemporaryOrder(models.Model):
    _name = 'temporary.order'

    product_tmpl_id = fields.Many2one('product.template', string="Product Template")
    product_variant_id = fields.Many2one('product.product', string="Product")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    location_id = fields.Many2one('stock.location', string="Location")
    reserve = fields.Float(string="Reserve")
    order_id = fields.Many2one('sale.order', 'Order')


class CustomerEnquiry(models.Model):
    _name = 'customer.enquiry.line'

    def _compute_prio_brand(self):
        for enquiry in self:
            enquiry.prior_brand_ids = enquiry.order_id.prior_brand_ids

    def _get_prio(self):
        for enquiry in self:
            if enquiry.order_id.partner_id:
                if enquiry.order_id.partner_id.prior_brand_ids:
                    return True
                else:
                    return False

    order_id = fields.Many2one('sale.order', 'Order')
    product_id = fields.Many2one('product.product', 'Product')
    prior_brand_ids = fields.Many2many('product.brand', string="Merk Prioritas", compute='_compute_prio_brand')
    brand_id = fields.Many2one('product.brand', 'Brand')
    lost = fields.Boolean("Lost")
    with_prio = fields.Boolean("Prio", default=_get_prio, readonly=False)
    name = fields.Char("Description")
    remarks = fields.Char("Remarks")
    rvd_sku = fields.Char('SKU')
    rvd_alias_id = fields.Many2one('rvd.product.alias', 'Alias')
    rvd_alias_line_id = fields.Many2one('rvd.product.alias.line', 'Key')
    rvd_attribute_ids = fields.Many2many('rvd.product.attribute', string='Attribute', domain="[('rvd_product_attribute_code_id', '!=', False)]")
    rvd_equipment_ids = fields.Many2many('product.equipment', string='Equipment', domain="[('rvd_product_equipment_code_id', '!=', False)]")
    rvd_equipment_id = fields.Many2one('product.equipment', 'Equipment', domain="[('rvd_product_equipment_code_id', '!=', False)]")
    quantity = fields.Integer('Quantity')
    is_attribute = fields.Boolean("Attributes")
    # attribute
    attr_height_min = fields.Float("Height Min")
    attr_height_max = fields.Float("Height Max", default=5.0)
    attr_height2_min = fields.Float("Height2 Min")
    attr_height2_max = fields.Float("Height2 Max", default=5.0)
    attr_od_min = fields.Float("OD Min")
    attr_od_max = fields.Float("OD Max", default=5.0)
    attr_od2_min = fields.Float("OD2 Min")
    attr_od2_max = fields.Float("OD2 Max", default=5.0)
    attr_id_min = fields.Float("ID Min")
    attr_id_max = fields.Float("ID Max", default=5.0)
    attr_id2_min = fields.Float("ID2 Min")
    attr_id2_max = fields.Float("ID2 Max", default=5.0)
    attr_gasket_od_min = fields.Float("Gasket OD Min")
    attr_gasket_od_max = fields.Float("Gasket OD Max", default=5.0)
    attr_thread_min = fields.Float("Thread Size")
    attr_thread_nut_min = fields.Float("Thread Nut Size Min")
    attr_flange_hat_min = fields.Float("Flange/Hat Min")
    attr_flange_hat_max = fields.Float("Flange/Hat Max", default=5.0)
    attr_lenght_min = fields.Float("Length Min")
    attr_lenght_max = fields.Float("Length Max", default=5.0)
    attr_lenght2_min = fields.Float("Length2 Min")
    attr_lenght2_max = fields.Float("Length2 Max", default=5.0)
    attr_widht_min = fields.Float("Widht Min")
    attr_widht_max = fields.Float("Widht Max", default=5.0)
    attr_widht2_min = fields.Float("Widht2 Min")
    attr_widht2_max = fields.Float("Widht2 Max", default=5.0)
    attr_bowl_thread_size_min = fields.Float("Bowl Thread Size")
    attr_litre_min = fields.Float("Litre Min")
    attr_litre_max = fields.Float("Litre Max", default=5.0)
    attr_ampere_min = fields.Float("Ampere Min")
    attr_ampere_max = fields.Float("Ampere Max", default=5.0)
    attr_desc = fields.Char("Description")
    attr_model = fields.Char("Model")
    attr_detail = fields.Char("Detail")
    attr_gasket_type = fields.Char("Gasket Type")


    # action to add product non stock
    def action_add_non_stock(self):
        view = self.env.ref('rvd_sale.product_non_stock_form_simple')
        non_stock = self.get_product_non_stock()
        context = dict(self.env.context)
        context.update({
            'order_id': self.order_id.id,
            'quantity': self.quantity,
        })
        return {
            'name': _('Non Stock'),
            'res_model': 'product.non.stock',
            'type': 'ir.actions.act_window',
            'views': [(view.id, 'form')],
            'res_id': non_stock.id,
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    def action_open_attrs(self):
        view = self.env.ref('rvd_sale.view_search_attribute')
        context = self._context
        return {
            'name': _('Customer Enquiry'),
            'res_model': 'customer.enquiry.line',
            'type': 'ir.actions.act_window',
            'views': [(view.id, 'form')],
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    def get_product_non_stock(self):
        non_stock_obj = self.env['product.non.stock']
        non_stock = non_stock_obj.search([('enquiry_id', '=', self.id)])
        if not non_stock:
            vals = self._prepare_line_non_stock(self.rvd_sku, self.quantity)
            temp = {
                'sku_name': self.rvd_sku,
                'enquiry_id': self.id,
                'non_stock_line_ids': [(0, 0, vals)]
            }
            non_stock = non_stock_obj.create(temp)
        return non_stock


    def _prepare_line_non_stock(self, name_sku, quantity):
        return {
            'product_char': name_sku,
            'quantity': quantity,
        }


    def create_attrs(self):
        context = self._context
        if context.get('active_model') == 'sale.order':
            self.write({
                'order_id': context.get('active_id'),
                'is_attribute': True,
            })
        return

    @api.onchange('product_id')
    def onchange_name_product(self):
        if self.product_id:
            self.name = self.product_id.name

    @api.onchange('prior_brand_ids')
    def onchange_is_priority(self):
        if self.prior_brand_ids:
            self.with_prio = True
        else:
            self.with_prio = False

    def search_product(self):
        # search ritma code
        ritma_codes = False
        # obj
        code_obj = self.env['rvd.product.code']
        att_obj = self.env['rvd.product.attribute']
        context = dict(self.env.context)
        # terbagi dua cara dalam search product di ritma code
        # 1.menggunakan attrbute
        # 2.mengguanakan nama sku atau equipment

        codes_list = []
        code_available = []
        if self.is_attribute or context.get('is_attribute'):
            # cek value attribute yang terisi
            value_fill_list = []
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
            elif self.attr_desc and self.attr_model and self.attr_detail and not self.attr_gasket_type:
                gasket_type = self.env.ref('rvd_product_code.gasket_type')
                ok = (1, 1, 1)
                value_fill_list.extend(ok)
                res_code =  code_obj.search([ 
                    ('description', 'like', self.attr_desc),
                    ('product_detail', 'like', self.attr_detail),
                    ('product_model', 'like', self.attr_model),
                ])
                if res_code:
                    for code in res_code:
                        codes_list.append(code.id)
            elif self.attr_desc and self.attr_model and not self.attr_detail and not self.attr_gasket_type:
                gasket_type = self.env.ref('rvd_product_code.gasket_type')
                ok = (1, 1, 1)
                value_fill_list.extend(ok)
                res_code =  code_obj.search([ 
                    ('description', 'like', self.attr_desc),
                    ('product_model', 'like', self.attr_model),
                ])
                if res_code:
                    for code in res_code:
                        codes_list.append(code.id)
            else:
                if self.attr_desc:
                    # ok = ()
                    value_fill_list.append(1)
                    description = self.env.ref('rvd_product_code.description')
                    attrs =  code_obj.search([ 
                        ('description', '=', self.attr_desc.upper()),
                    ])
                    if attrs:
                        for code in attrs:
                            codes_list.append(code.id)
                # model
                if self.attr_model:
                    value_fill_list.append(1)
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
                # detail
                if self.attr_detail:
                    value_fill_list.append(1)
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
                # gasket type
                if self.attr_gasket_type:
                    value_fill_list.append(1)
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

            if codes_list:
                for code in codes_list:
                    if self.attr_height_min != 0.0 and min_height:
                        value_fill_list.append(1)
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
                        value_fill_list.append(1)
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
                        value_fill_list.append(1)
                        od_id = self.env.ref('rvd_product_code.od')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', od_id.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '>', min_od),
                            ('value_int', '<', max_od),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_od2_min != 0.0 and min_od2:
                        value_fill_list.append(1)
                        od_id = self.env.ref('rvd_product_code.od2')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', od_id.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '>', min_od2),
                            ('value_int', '<', max_od2),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_id_min != 0.0 and min_id:
                        value_fill_list.append(1)
                        id_id = self.env.ref('rvd_product_code.id')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', id_id.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '>', min_id),
                            ('value_int', '<', max_id),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_id2_min != 0.0 and min_id2:
                        value_fill_list.append(1)
                        id_id = self.env.ref('rvd_product_code.id2')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', id_id.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '>', min_id2),
                            ('value_int', '<', max_id2),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_gasket_od_min != 0.0 and gasket_od_min:
                        value_fill_list.append(1)
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
                        value_fill_list.append(1)
                        thread_size = self.env.ref('rvd_product_code.thread_size')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', thread_size.id),
                            ('rvd_product_attribute_code_id', '!=', code),
                            ('value_int', '=', self.attr_thread_min),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_thread_nut_min != 0.0:
                        value_fill_list.append(1)
                        thread_nut_size = self.env.ref('rvd_product_code.thread_nut_size')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', thread_nut_size.id),
                            ('rvd_product_attribute_code_id', '!=', code),
                            ('value_int', '=', self.attr_thread_nut_min),
                        ])
                        if attrs:
                            list_avail.append(1)

                    if self.attr_flange_hat_min != 0.0 and flange_hat_min:
                        value_fill_list.append(1)
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
                        value_fill_list.append(1)
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
                        value_fill_list.append(1)
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
                        value_fill_list.append(1)
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
                        value_fill_list.append(1)
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
                        value_fill_list.append(1)
                        bowl_thread = self.env.ref('rvd_product_code.bowl_thread_size')
                        attrs =  self.env['rvd.product.attribute'].search([
                            ('attribute_alias_id', '=', bowl_thread.id),
                            ('rvd_product_attribute_code_id', '=', code),
                            ('value_int', '=', self.attr_bowl_thread_size_min),
                        ])
                        if attrs:
                            list_avail.append(1)

                if len(list_avail) >= 1:
                    code_available.append(code)
            elif not codes_list:
                raise ValidationError(_("Product Not Found"))

            if len(value_fill_list) < 4:
                raise ValidationError(_("Fill Attribute Minimum 4"))

            else:
                with_prio = context.get('default_is_attribute')
                if code_available or codes_list:
                    result = []
                    res_product = []
                    if codes_list:
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
                    else:
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


                    for res_id in result:
                        product = self.env['product.template'].browse(res_id)
                        description = ' '
                        onhand = product.with_context(warehouse=self.order_id.warehouse_id.id).qty_available
                        if onhand <= 0:
                            description += 'Stock: ' + str(onhand) + ', ' +self.order_id.warehouse_id.code.upper() + ' Out of Stock'
                        elif onhand < self.quantity:
                            description += 'Stock: ' + str(onhand) + ', ' + self.order_id.warehouse_id.code.upper() + ' Stock less than request.'
                        elif onhand > self.quantity:
                            description += 'Stock: ' + str(onhand) + ', ' + self.order_id.warehouse_id.code.upper() + ' Ready'

                        # attribute
                        height = 0.0
                        height2 = 0.0
                        od1 = 0.0
                        od2 = 0.0
                        id1 = 0.0
                        id2 = 0.0
                        flange_hat = 0.0
                        length = 0.0
                        length2 = 0.0
                        width = 0.0
                        width2 = 0.0
                        thread = 0.0
                        litre = 0.0
                        ampere = 0.0
                        for attr in product.rvd_product_attributes_ids:
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.height'):
                                height = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.height2'):
                                height2 = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.od'):
                                od1 = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.od2'):
                                od2 = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.id'):
                                id1 = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.id2'):
                                id2 = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.flange_hat'):
                                flange_hat = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.length'):
                                length = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.length2'):
                                length2 = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.width'):
                                width = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.width2'):
                                width2 = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.thread_size'):
                                thread = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.litre'):
                                litre = attr.value_int
                            if attr.attribute_alias_id == self.env.ref('rvd_product_code.ampere'):
                                ampere = attr.value_int

                        res_product.append((0, 0, {
                            'reserve': self.quantity,
                            'product_tmpl_id': product.id,
                            'product_variant_id': product.product_variant_id.id,
                            'ritma_code_id': product.rvd_product_template_code_id.id,
                            'brand_id': product.product_brand_id.id,
                            'price': product.list_price,
                            'description': product.rvd_product_template_code_id.description,
                            'order_id': self.order_id.id,
                            'desc_stock': description,
                            'is_attribute' : self.is_attribute,
                            'height': height,
                            'height2': height,
                            'od1': od1,
                            'od2': od2,
                            'id1': id1,
                            'id2': id2,
                            'flange_hat': flange_hat,
                            'length': length,
                            'length2': length2,
                            'width': width,
                            'width2': width2,
                            'thread': thread,
                            'litre': litre,
                            'ampere': ampere,

                        }))

                    wiz = self.env['result.product'].create({
                        'section_name': "Attribute",
                        'rvd_sku': self.rvd_sku,
                        'brand_id': self.brand_id.id,
                        'ritma_code_ids': codes_list,
                        'rvd_attribute_ids': self.rvd_attribute_ids.ids,
                        'rvd_equipment_ids': self.rvd_equipment_id.ids,
                        'rvd_product_sku_ids': res_product,
                        'is_attribute': True,
                    })
                    view = self.env.ref('rvd_sale.view_result_product_form_attribute')
                    context.update({
                        'product_list': result,
                        'enquiry_id': self.id,
                        'sku': self.rvd_sku,
                        'attributes': self.rvd_attribute_ids.ids,
                        'equipment': self.rvd_equipment_id.ids,
                        'order': self.order_id.id,
                        'sku_result_ids': wiz.rvd_product_sku_ids.ids,
                        'limit_quantity': self.quantity,
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
        elif not self.is_attribute or context.get('is_attribute'):
            if self.rvd_sku and not self.brand_id and not self.rvd_equipment_id and not self.rvd_attribute_ids:
                ritma_codes = code_obj.search([
                    ('cross_reference_ids.processed_name', '=', self.rvd_sku),
                ])
            elif self.rvd_attribute_ids or self.rvd_equipment_id or self.brand_id:
                # attribute or equipment not false
                if self.rvd_sku:
                    ritma_codes = code_obj.search([
                        '|', ('cross_reference_ids.processed_name', '=', self.rvd_sku),
                        ('product_equipment_ids', 'in', self.rvd_equipment_id.ids),
                    ])
                else:
                    ritma_codes = code_obj.search([
                        '|', ('rvd_product_attributes_ids', 'in', self.rvd_attribute_ids.ids),
                        ('product_equipment_ids', 'in', self.rvd_equipment_id.ids),
                    ])

        if ritma_codes:
            result = []
            res_product = []
            for code in ritma_codes:
                code_list = []
                if self.with_prio:
                    for brand_id in self.prior_brand_ids:
                        for product in code.product_tmpl_ids.filtered(lambda x: x.product_brand_id == brand_id):
                            result.append(product.id)
                else:
                    for product in code.product_tmpl_ids:
                        result.append(product.id)

            # create data wizard

            for res_id in result:
                product = self.env['product.template'].browse(res_id)
                description = ' '
                onhand = product.with_context(warehouse=self.order_id.warehouse_id.id).qty_available
                if onhand <= 0:
                    description += 'Stock: ' + str(onhand) + ', ' + self.order_id.warehouse_id.code.upper() + ' Out Of Stock.'
                elif onhand < self.quantity:
                    description += 'Stock: ' + str(onhand) + ', ' + self.order_id.warehouse_id.code.upper() + ' Stock less than request.'
                elif onhand > self.quantity:
                    description += 'Stock: ' + str(onhand) + ', ' + self.order_id.warehouse_id.code.upper() + ' Ready.'

                res_product.append((0, 0, {
                    'product_tmpl_id': product.id,
                    'product_variant_id': product.product_variant_id.id,
                    'ritma_code_id': product.rvd_product_template_code_id.id,
                    'brand_id': product.product_brand_id.id,
                    'price': product.list_price,
                    'description': product.rvd_product_template_code_id.description,
                    'order_id': self.order_id.id,
                    'desc_stock': description,
                    'reserve': self.quantity,
                }))

            wiz = self.env['result.product'].create({
                'section_name': self.rvd_sku or self.rvd_equipment_id.name,
                'rvd_sku': self.rvd_sku,
                'brand_id': self.brand_id.id,
                'ritma_code_ids': ritma_codes.ids,
                'rvd_attribute_ids': self.rvd_attribute_ids.ids,
                'rvd_equipment_ids': self.rvd_equipment_id.ids,
                'rvd_product_sku_ids': res_product,
            })

            context.update({
                'product_list': result,
                'enquiry_id': self.id,
                'sku': self.rvd_sku,
                'attributes': self.rvd_attribute_ids.ids,
                'equipment': self.rvd_equipment_id.ids,
                'order': self.order_id.id,
                'sku_result_ids': wiz.rvd_product_sku_ids.ids,
                'limit_quantity': self.quantity,
            })
            view = self.env.ref('rvd_sale.view_result_product_form')
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
            raise ValidationError(_("Product is not found, please check SKU"))
