{
    "name": "Bulk Quiz Import by Section",
    "version": "1.0",
    "author": "Raghib Khesal",
    "depends": ["base", "website_slides"],
    "category": "Education",
    "license": "LGPL-3",
    "summary": "Import quizzes and assign to course sections",
    "data": [
        "security/ir.model.access.csv", #base.group_system
        "views/quiz_import_wizard_view.xml",
        "views/menu.xml",
        "views/slide_channel_views.xml"
    ],
    "installable": True,
    "application": True
}