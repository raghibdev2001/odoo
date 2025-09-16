{
    'name': 'eLearning Mobile API',
    'version': '1.0',
    'category': 'eLearning',
    'author': 'Raghib Khesal',
    'summary': 'REST API for Mobile App with JWT Authentication',
    'depends': ['base', 'website_slides', 'mail', 'auth_signup'],
    'data': [
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': False,
}
