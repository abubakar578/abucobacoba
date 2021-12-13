# -*- coding: utf-8 -*-
{
    'name': 'Rivindi - Sale',
    'version': '14.0.1.0.0',
    'license': 'OPL-1',
    'summary': 'Rivindi - Sales',
    'category': 'Product',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description': '''
    ''',
    'depends': [
        'rvd_product_code',
        'sale',
        'stock',
        'delivery',
        'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/route.xml',
        'views/sale_view.xml',
        'views/pricelist_view.xml',
        'views/delivery_carrier_view.xml',
        'views/ritma_shipping_views.xml',
        'wizard/result_product_view.xml',
        'wizard/product_non_stock_views.xml',
        'wizard/choose_delivery_views.xml',
    ],
    'demo': [
    ],
    'application': False,
}
