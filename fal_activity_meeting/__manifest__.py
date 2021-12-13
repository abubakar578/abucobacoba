# -*- coding: utf-8 -*-
{
    "name": "Meeting Timesheet From Schedule Activity",
    'version': '14.0.1.0.0',
    'license': 'OPL-1',
    'summary': "create Meeting Timesheet From Schedule Activity",
    'category': "HR",
    'author': "CLuedoo",
    'website': "https://www.cluedoo.com",
    'support': 'cluedoo@falinwa.com',
    "description": """
        Meeting Timesheet From Schedule Activity.
        ===============================================================
        Module create Meeting Timesheet From Schedule Activity.
    """,
    'depends': [
        'fal_calendar_meeting_ext',
        'calendar',
    ],
    # always loaded
    'data': [
        'views/activity_meeting_view.xml',
        'views/assets.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'demo': [],
    'css': [],
    'js': [],
    'qweb': [
        'static/src/xml/templates.xml',
    ],
    'price': 0.00,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}
