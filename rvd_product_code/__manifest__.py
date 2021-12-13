# -*- coding: utf-8 -*-
{
    'name': 'Rivindi Product Code',
    'version': '14.0.1.0.0',
    'license': 'OPL-1',
    'summary': 'Rivindi Product Code',
    'category': 'Product',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description': '''
    ''',
    'depends': [
        'rvd_product_web_data',
        'stock',
    ],
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/fal_product_views.xml',
        'wizard/edit_cross.xml',
        'wizard/merge_brand_views.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'application': False,
}
