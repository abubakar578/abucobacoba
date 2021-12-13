# -*- coding: utf-8 -*-
{
    'name': "Sale Approval.",
    'version': '14.0.1.0.0',
    'license': 'OPL-1',
    'summary': "Extra Approval Step on Sales.",
    'sequence': 20,
    'category': 'Sales',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description': """
        Extra Approval Step on Sales.
        ===============================================================
        Add Waiting Approval stages on sales order. There is 2 option available:
        1. Always using proposal
        2. Can skip the proposal process
    """,
    'depends': ['sale_management'],
    'data': [
        "views/sale_views.xml",
    ],
    'images': [
        'static/description/1_screenshot.png'
    ],
    'demo': [
    ],
    'price': 360.00,
    'currency': 'EUR',
    'application': False,
}