# -*- coding: utf-8 -*-
{
    'name': "Credit Limit Formula",
    'version': '14.0.1.0.0',
    'license': 'OPL-1',
    'summary': "Restriction and Warning of Credit Limit based on percentage Formula.",
    'sequence': 20,
    'category': 'Sales',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description': """
        Restriction and Warning of Credit Limit based on percentage Formula.
        ===============================================================
        On top of Our Credit Limit Module, we add advanced feature to forcefully block any transaction if
        customer already reach the limit of credit restriction. User can also make a warning,
        and still convert the sales order to proposal stage
    """,
    'depends': ['fal_partner_credit_limit'],
    'data': [
        'security/ir.model.access.csv',
        'views/partner_view.xml',
        'wizard/fal_alert_wizard_view.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'price': 360.00,
    'currency': 'EUR',
    'application': False,
}
