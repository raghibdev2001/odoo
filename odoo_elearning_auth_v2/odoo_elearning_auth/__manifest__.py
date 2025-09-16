# -*- coding: utf-8 -*-
{
    'name': 'eLearning Auth API - Along with course Detail',
    'version': '1.0',
    'author':   "Raghib Khesal",
    'summary': 'Mobile API for user signup, login, OTP verification, password reset with JWT',
    'category': 'Auth',
    'depends': ['base', 'mail'],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'data/email_templates.xml'
    ],
    'installable': True,
    'applications': True,
}