{
    'name': 'My Custom Slide_Sequential Slide Unlock',
    'description': 'Only allow the user to view the next slide after completing the previous one.',
    'category': 'eLearning',
    'author': 'Raghib Khesal',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['website_slides'],
    'data': [
        'views/slide_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # Include JS if needed later
        ],
    },
    'installable': True,
    'application': False,
}