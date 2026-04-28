# -*- coding: utf-8 -*-
{
    # App information
    'name': 'My Library',
    'category': 'Tools',
    'version': '18.0.1.0',
    'summary': 'Custom library management module.',
    'license': 'OPL-1',

    # Dependencies
    'depends': ['base'],

    # Views
    'data': [
        'security/lib_group.xml',
        'security/ir.model.access.csv',
        'security/lib_group.xml',
        'wizard/borrow_wizard.xml',
        'views/book.xml',
        'report/book_report.xml',
    ],

    # Author
    'author': 'Ayushi Jadav',
    'website': '',
    'maintainer': 'Ayushi Jadav',

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
