from odoo import models, fields, api, _
from odoo.exceptions import UserError
import re
import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    # @api.depends("name")
    # # Processed Name is a Char field that is similar to Name, but without special character
    # def _get_processed_name(self):
    #     for contact in self:
    #         name = contact.name
    #         contact.processed_name = re.sub(r'[^\w]', '', name)

    # processed_name = fields.Char("Processed Name", compute="_get_processed_name", store=True)

    def set_verified(self):
        self.is_verified = True

    def _can_edit_view(self):
        can_edit = False
        if self.is_verified:
            if self._uid in self.env.ref('account.group_account_user').users.ids:
                can_edit = True
            else:
                can_edit = False
        else:
            can_edit = True
        return can_edit

    def _compute_can_edit_view(self):
        for partner in self:
            if partner.is_verified:
                if self._uid in self.env.ref('account.group_account_user').users.ids:
                    partner.can_edit_form = True
                else:
                    partner.can_edit_form = False
            else:
                partner.can_edit_form = True

    can_edit_form = fields.Boolean('Can Edit', default=_can_edit_view, compute='_compute_can_edit_view')
    is_verified = fields.Boolean('Verified')
    extension = fields.Text(string="Extension")
    cabang_id = fields.Many2one("res.country.state", string='Cabang', domain="[('country_id', '=?', country_id)]")
    klasifikasi_customer = fields.Selection(
        [('retail', 'Retail'),
         ('user', 'User'),
         ('dealer1', 'Dealer 1'),
         ('dealer2', 'Dealer 2'),
         ('dealer3', 'Dealer 3'),
         ('project', 'Project'), 
        ], string="Klasifikasi Customer")
    
    email_domain = fields.Char('Email Domain', readonly=False, store=True, compute='_email_domain')
    # Saham
    saham_id = fields.Many2one('res.users', string='Saham')
    ktp = fields.Char('No KTP')
    owner_saham_ids = fields.One2many('res.partner', 'saham_id', string='Pemegang Saham')
    jumlah_saham = fields.Integer("Jumlah Saham %")
    # Penaggung Jawab
    penanggung_id = fields.Many2one('res.users', string='Penanggung Jawab')
    penanggung_jawab_ids = fields.One2many('res.partner', 'penanggung_id', string='Penanggung Jawab')
    # Bank
    # bank_ids = fields.One2many('rvd.bank', 'partner_id', string='Bank')
    # umum
    main_address = fields.Many2one('res.partner', string='Main Address', domain="[('parent_id', '=', id), ('type', 'not in', ['delivery', 'invoice'])]")
    delivery_address = fields.Many2one('res.partner', string='Delivery Address', domain="[('parent_id', '=', id), ('type', '=', 'delivery')]")
    invoices_address = fields.Many2one('res.partner', string='Invoice Address', domain="[('parent_id', '=', id), ('type', '=', 'invoice')]")
    sales_admin_id = fields.Many2one('res.users', string='CSS')
    rvd_parent_id = fields.Many2one('res.partner', string='Related Company', index=True)
    rvd_child_ids = fields.One2many('res.partner', 'rvd_parent_id', string='Contacts', domain=[('active', '=', True)]) 
    phone_1 = fields.Char('Phone 1')
    phone_2 = fields.Char('Phone 2')
    phone_3 = fields.Char('Phone 3')
    phone_3 = fields.Char('Phone 3')
    fax = fields.Char('Fax')
    receipt = fields.Boolean('Receipt')
    receipt_combined = fields.Boolean('Receipt Combined')
    invoice_by_fax = fields.Boolean('Invoice by Fax')
    stamp = fields.Boolean('Stamp')
    invoice_by = fields.Selection(
        [('head', 'Head Office'),
         ('subsidiary', 'Subsidiary'),
        ], string="Invoices By", default='head')
    invoice_area = fields.Selection(
        [('nort', 'North'),
         ('south', 'South'),
         ('east', 'East'),
         ('weast', 'Weast'),
         ('central', 'Central'),
        ], string="Invoices Area", default='central')
    book = fields.Integer('Book')
    pages = fields.Integer('Page')
    tgl_do = fields.Selection(
        [('boleh', 'Diperbolehkan'),
         ('tidak_boleh', 'Tidak Diperbolehkan'),
        ], string="Tanggal DO & Invoice Berbeda", default='boleh')
    invoice_diterbitkan = fields.Selection(
        [('partial', 'Partial PO'),
         ('full', 'Full PO'),
        ], string="Invoice DIterbitkan dan Penagihan", default='partial')
    lampiran_tanda_terima = fields.Selection(
        [('do', 'DO...rangkap'),
         ('invoice', 'Invoice...rangkap'),
         ('po', 'Fotocopy PO...rangkap'),
         ('pajak', 'Faktur Pajak...rangkap'),
        ], string="Lampiran Tanda Terima Tagihan", default='do')
    stampel_rekening_bank = fields.Selection(
        [('all_invoice', 'Semua Invoice'),
         ('info', 'Informasi Awal Transaksi'),
        ], string="Stampel Rekening Bank Perusahaan", default='all_invoice')
    status_usaha = fields.Selection(
        [('sendiri', 'Milik Sendiri'),
         ('sewa', 'Sewa'),
        ], string="Status Tempat Usaha", default='sendiri')
    jenis_usaha = fields.Selection(
        [('pt', 'Perseroan Terbatas/PT'),
         ('cv', 'CV'),
         ('dagang', 'Usaha Dagang/Perusahaan Dagang'),
         ('tbk', 'Perseroan Terbatas/TBK'),
         ('toko', 'Toko'),
        ], string="Jenis Usaha", default='pt')
    pic_barang = fields.Boolean('PIC Penerima Barang & Stempel')
    tgl_berdiri = fields.Date('Tanggal Berdiri')

    # ekspedisi
    ekspedisi = fields.Boolean('Ekspedisi')
    follow_up = fields.Boolean('Follow Up')
    pembayaran = fields.Selection(
        [('perusahaan', 'Perusahaan'), 
         ('konsumen', 'Konsumen'),
        ], string="Pembayaran", default='perusahaan')
    shipping_ids = fields.Many2many('delivery.carrier', string='Shipping')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')

    # pembayaran
    payment_term_id = fields.Many2one("account.payment.term", string='Standar Termin')
    option_due_date = fields.Selection([
            ('day_after_invoice_date', "days after the invoice date"),
            ('after_invoice_month', "days after the end of the invoice month"),
            ('day_following_month', "of the following month"),
            ('day_current_month', "of the current month"),
        ], compute='_default_option_due_date', string='Jatuh Tempo')

    # Accounting
    npkp = fields.Char('NPKP')
    date_npkp = fields.Date('Tanggal Pengukuhan')
    kode_transaksi = fields.Selection(
        [('selain_pemungut_ppn', 'Selain Pemungut PPN'),
        ], string="Kode Transaksi", default='selain_pemungut_ppn')
    kode_status = fields.Selection(
        [('normal', 'Normal'),
        ], string="Kode Status", default='normal')
    nik = fields.Integer('NIK')
    ppn = fields.Boolean('PPN')
    date_receive_invoice = fields.Date('Jadwal Tanda Terima Tagihan')
    date_payment_invoice = fields.Date('Jadwal Pembayaran Tagihan')
    faktur = fields.Selection(
        [('email', 'Email'),
        ('lampiran', 'Dilampirkan dalam Lampiran Tanda Terima'),
        ], string="Faktur Pajak", default='email')

    # Remarks
    remarks_1 = fields.Text('Catatan 1')
    remarks_2 = fields.Text('Catatan 2')

    # Harga Jual
    blue_price_item = fields.Selection(
        [('up_retail_pi', 'Up  Retail Price'),
        ], string="Blue Price Item", default='up_retail_pi')
    rounded_price_item = fields.Boolean('Rounded Price Item')
    rounded_blue_price = fields.Selection(
        [('up_retail_rd', 'Up  Retail Price'),
        ], string="Support/Net Price Item", default='up_retail_rd')
    harga_customer = fields.Boolean('Berlaku Harga Kuota')
    harga_support = fields.Boolean('Berlaku Harga Support')
    tm = fields.Float('% TM')

    # document
    rvd_documents_ids = fields.One2many('rvd.document', 'partner_id', string="Document")

    branch_name = fields.Char(string="Branch ID")
    adj_cust_price = fields.Selection([
        ('induk', 'Induk'),
        ('cabang', 'Cabang'),
        ], string="Harga Customer Sesuai", default='induk')
    service_lvl = fields.Selection([
        ('regular', 'Reguler'),
        ('price_contract', 'Price Contract'),
        ('price_contract_qty', 'Price Contract & Qty'),
        ('con_vhs', 'Consignment VHS'),
        ('con_non_vhs', 'Consignment Non VHS'),
        ], string="Service Level")
    contract_period = fields.Date(string="Masa Berlaku Kontrak")
    cust_type = fields.Selection([
        ('project', 'Project'),
        ('non_project', 'Non Project'),
        ], string="Tipe Customer")
    prior_brand_ids = fields.Many2many('product.brand', 'prior_brand_rel', 'prior_brand', string="Merk Prioritas")
    reserved_brand_ids = fields.Many2many('product.brand', 'reserved_brand_rel', 'reserved_brand', string="Merk Cadangan")
    cust_attachment = fields.Boolean(string="Lampiran Customer")

    # _sql_constraints = [
    #     ('name_contact_uniq', 'unique(processed_name)',
    #      "Name Doesn't exist"),
    # ]

    @api.depends('payment_term_id')
    def _default_option_due_date(self):
        for item in self:
            if item.payment_term_id:
                item.option_due_date = item.payment_term_id.line_ids[0].option
            else:
                item.option_due_date = 'day_after_invoice_date'

    @api.depends('email', 'is_company')
    def _email_domain(self):
        for item in self:
            if item.is_company and item.email:
                domain = item.email.split('@')
                _logger.info("XXXXXXXXXX")
                _logger.info(len(domain))
                if len(domain) < 2:
                    raise UserError("Please check your email")
                item.email_domain = domain[1]
                if '>' in domain[1]:
                    check_domain = domain[1].split('>')
                    item.email_domain = check_domain[0]
            else:
                item.email_domain = False


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    ship_via = fields.Selection(
        [('darat', 'Darat'), 
         ('laut', 'Laut'),
         ('udara', 'Udara'),
        ], string="Ship", default='darat')
    vendor_id = fields.Many2one("res.partner", string='Vendor', domain="[('parent_id', '=', False), ('type', '=', 'delivery')]")
    pembayaran = fields.Selection(
        [('perusahaan', 'Perusahaan'), 
         ('konsumen', 'Konsumen'),
        ], string="Pembayaran", default='perusahaan')

    @api.onchange('vendor_id')
    def change_name_with_vendor(self):
        name = ''
        if self.vendor_id:
            name = self.vendor_id.name
            if self.ship_via:
                ship_name = dict(self._fields['ship_via'].selection).get(self.ship_via)
                name = self.vendor_id.name + ' [' + ship_name + ']'
            self.name = name


class AddDocument(models.Model):
    _name = 'rvd.document'

    name = fields.Char("Name")
    partner_id = fields.Many2one('res.partner', string='Partner')
    create_date = fields.Date('Create Date', default=fields.date.today())
    exp_date = fields.Date('Expired Date')
    remarks = fields.Char('Remarks')
    document = fields.Binary(string="Document")


# class BankPerusahaan(models.Model):
#     _name = 'rvd.bank'

#     name = fields.Char("Name")
#     partner_id = fields.Many2one('res.partner', string='Partner')
#     no_rekening = fields.Integer("No Rekening")
#     cabang = fields.Char("Cabang")
#     fasilitas = fields.Char("Tipe Fasilitas")
