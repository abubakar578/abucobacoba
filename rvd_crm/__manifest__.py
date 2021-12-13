# -*- coding: utf-8 -*-
{
    'name': 'Rivindi - CRM',
    'version': '14.0.1.0.0',
    'license': 'OPL-1',
    'summary': 'Rivindi CRM',
    'category': 'CRM',
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    'description': '''
    ''',
    'depends': [
        'rvd_product_code',
        'sale_crm',
        'rvd_sale',
        'kanban_draggable',
        'rvd_master_customer',
        'fal_calendar_meeting_ext',
        'fal_activity_meeting',
    ],
    'data': [
        'data/crm_stage_data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'report/crm_activity_report.xml',
        'views/calendar_view.xml',
        'views/crm_lead_views.xml',
        'views/tracking_stage_views.xml',
        'views/crm_report_sales.xml',
        'wizard/result_product_view.xml',
    ],
    'images': [
    ],
    'demo': [
    ],
    'application': False,
}
