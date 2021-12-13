from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = 'res.partner'

    def write(self, values):
        # change title and name
        if values.get('title') and values.get('name'):
            title_id = self.env['res.partner.title'].browse(values.get('title'))
            title_name = title_id.shortcut + '. ' + values.get('name')
            values.update({'name': title_name.upper()})
        # change name not title
        elif values.get('name') and not values.get('title'):
            title_name = values.get('name')
            if self.title:
                title_name = self.title.shortcut + '. ' + values.get('name')
            values.update({'name': title_name.upper()})
        # change title not name
        elif values.get('title') and not values.get('name'):
            title_id = self.env['res.partner.title'].browse(values.get('title'))
            display_name = self.name.split(". ")
            title_name = title_id.shortcut + '. ' + display_name[1]
            values.update({'name': title_name.upper()})
        return super(Partner, self).write(values)


    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if val.get('company_type'):
                if val['company_type'] == 'company' and val['title']:
                    title_id = self.env['res.partner.title'].browse(val['title'])
                    title_name = title_id.shortcut + '. ' + val['name']
                    val['name'] = title_name.upper()

        return super(Partner, self).create(vals_list)


class CompanyTitle(models.Model):
    _inherit = 'res.partner.title'

    fal_is_company = fields.Boolean(string='Is Company', Default=False)
