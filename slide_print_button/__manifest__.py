{
    "name": "Course Slide Print Button",
    "version": "1.0",
    "summary": "Adds Print button for DOCX, PDF, and image slides",
    'category': 'eLearning',
    'author': 'Raghib Khesal',
    "depends": ["website_slides"],
    "data": [
        "views/slide_templates.xml"
    ],
    "assets": {
        "web.assets_frontend": [
            "/slide_print_button/static/src/js/print_button.js"
        ]
    },
    "installable": True,
    "application": False
}
