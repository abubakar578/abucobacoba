# encoding: utf-8
# Part of Odoo - CLuedoo Edition. Ask Falinwa / CLuedoo representative for full copyright And licensing details.
{
    "name": "Meeting Calendar Enhancement",
    "version": "14.0.1.0.0",
    'license': 'OPL-1',
    'summary': 'Manage your meetings',
    'sequence': 130,
    'category': 'Extra Tools',
    'author': 'CLuedoo',
    'website': 'https://www.cluedoo.com',
    'support': 'cluedoo@falinwa.com',
    "description": """
        Module to improve meeting functions
        ======================================

        12.1.0.0.0 - First V.12 Release
        12.1.1.0.0 - Bug Fix on Security Side
        12.2.0.0.0 - Adding Option not to automatically send email
        12.5.0.0.0 - Add action to send MOM email and dependencies to fal_block_automatic_email
        13.0.1.0.0 - Migration
        14.0.1.0.0 - migration, add field state (no more available in v14), view management, remove double validation. can make it via studio in v14
    """,
    'depends': [
        # 'fal_auto_block_email',
        'calendar',
        'account',
        'contacts',
        'hr',
        'fal_calendar_config',
    ],
    'init_xml': [],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/fal_meeting_meter_data.xml',
        'data/fal_meeting_meter_config.xml',
        'data/fal_mom_template_data.xml',
        'views/calendar_event.xml',
        'views/res_config_views.xml',
        'views/res_partner_view.xml',
        'views/menu.xml',
        'wizard/fal_calendar_meeting_wizard_view.xml',
        'report/calendar_meeting_mom_report.xml',
        'report/calendar_meeting_public_mom_report.xml',
        'report/calendar_meeting_internal_mom_report.xml',
    ],
    'images': [
        'static/description/meeting_screenshot.png'
    ],
    'demo': [],
    'css': [],
    'js': [],
    'qweb': [],
    'price': 540.00,
    'currency': 'EUR',
    'installable': True,
    'active': False,
    'application': False,
    'auto_install': False,
    'post_init_hook': '',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
