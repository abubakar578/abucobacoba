# -*- coding: utf-8 -*-
# Part of Odoo Falinwa Edition.
# See LICENSE file for full copyright and licensing details.
{
    'name': 'Partner Credit Limit',
    'version': '14.0.1.0.0',
    'license': 'OPL-1',
    'summary': 'Partner Credit Limit',
    'sequence': 21,
    'category': 'Sales',
    'author': 'CLuedoo',
    'website': 'https://www.cluedoo.com',
    'support': 'cluedoo@falinwa.com',
    'description': """
        Module to give Credit Limit feature on partner.
        Credit Limit will be based on 2 parameter
        1. Total Number
        2. Aged Credit
        3. Both
    """,
    'depends': [
        'fal_sale_approval',
    ],
    'data': [
        # "wizard/sale_proposal_wizard_views.xml",
        'views/partner_view.xml',
    ],
    'images': [
        'static/description/fal_partner_credit_limit_screenshot.png'
    ],
    'installable': True,
    'active': True,
    'price': 810.00,
    'currency': 'EUR',
    'application': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
