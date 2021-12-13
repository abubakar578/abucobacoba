# -*- coding: utf-8 -*-
{
    'name': 'Base Setup Config',
    'version': '14.0.1.0.0',
    'license': 'OPL-1',
    'summary': 'Base Setup Configuration',
    'category': '',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description': """
    """,
    'depends': [
        'base_setup',
        'product',
    ],
    'init_xml': [],
    'data': [
        'security/ir.model.access.csv',
        'wizard/need_help_wizard_view.xml',
        'views/base_setup_config_settings_view_form.xml',
    ],
    'demo': [],
    'css': [],
    'js': [],
    'installable': True,
    'application': False,
    'auto_install': True,
}
