# encoding: utf-8
# Part of Odoo - CLuedoo Edition. Ask Falinwa / CLuedoo representative for full copyright And licensing details.
{
    'name': "Company Title",
    'version': '14.0.1.0.0',
    'license': 'OPL-1',
    # 'sequence': 18,
    'category': 'Contacts',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description': """
Company Title
===============================================================
Enable title for partner (Company).
    """,
    'depends': [
        'contacts',
    ],
    'data': [
        'data/res_partner_data.xml',
        'views/res_partner_views.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'price': 10.00,
    'currency': 'EUR',
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
