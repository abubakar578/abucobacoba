# -*- coding: utf-8 -*-
{
    'name': 'Rivindi - Master Customer',
    'version': '14.0.1.0.0',
    'license': 'OPL-1',
    'summary': 'Rivindi Customer',
    'category': 'CRM',
    'sequence': 10,
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description': '''
    ''',
    'depends': [
        'account',
        'contacts',
        'crm',
        'delivery',
        'fal_group_by_commercial',
        'fal_partner_credit_limit',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'application': False,
}
