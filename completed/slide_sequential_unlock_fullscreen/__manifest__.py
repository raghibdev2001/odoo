{
    'name': 'Slide Sequential Unlock Fullscreen',
    'summary': 'Progressive unlock slides based on previous completion',
    'version': '1.0',
    'author': 'Raghib Khesal',
    'category': 'Website/Elearning',
    'license': 'LGPL-3',
    'depends': ['website_slides'],
    'data': [
        'views/slide_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            # any assets you use (optional)
        ],
    },
    'installable': True,
    'application': False,
}