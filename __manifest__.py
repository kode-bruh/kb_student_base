# -*- coding: utf-8 -*-
{
    'name': "Student Management",

    'summary': "Student Management",

    'description': """
Provide users the ability to track and manage students' information such as classes, activities, behavior notes, etc.
    """,

    'author': "Kode-Bruh",
    'website': "https://www.kode-bruh.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Student Management',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['mail', 'portal'],

    # always loaded
    'data': [
        'security/security_group.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/kb_document_type.xml',
        'views/kb_application.xml',
        'views/kb_application_stage.xml',
        'views/kb_application_document_template.xml',
        'views/kb_student_document.xml',
        'views/kb_class.xml',
        'views/kb_class_history.xml',
        'views/kbw_class_history_create.xml',
        'views/kb_school.xml',
        'views/kb_student.xml',
        'views/kb_term.xml',
        'views/portal_kb_application.xml',
        'views/res_config_settings.xml',
        'views/menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'application': True,
    'price': 99.9,
    'currency': 'USD',
}

