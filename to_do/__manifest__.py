# -*- coding: utf-8 -*-
{
    # App information
    'name': 'My ToDo List App',
    'category': 'Tools',
    'version': '18.0.1.0',
    'summary': 'Custom todo list management module to track tasks and deadlines.',
    'license': 'OPL-1',

    # Dependencies
    'depends': ['base'],

    # Views
    'data': [
        'security/ir.model.access.csv',
        'views/to_do.xml',
    ],

    # Author
    'author': 'Ayushi',
    'website': '',
    'maintainer': 'Ayushi',

    # Technical
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,

    # Store fields (optional, safe to keep but not needed locally)
    'images': [],
    'live_test_url': '',
    'price': 199,
    'currency': 'EUR',
}
