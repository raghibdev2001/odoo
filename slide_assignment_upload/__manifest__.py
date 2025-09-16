{
    "name": "Slide Assignment Upload",
    "summary": "Upload assignments and manually assign points for Odoo eLearning",
    "version": "1.0",
    "category": "eLearning",
    "author": "Raghib Khesal",
    "depends": ["website_slides"],
    "data": [
        "security/ir.model.access.csv",
        "views/slide_assignment_views.xml",
        "views/slide_assignment_templates.xml",
        "views/website_slides_templates_inherit.xml",
    ],
    "installable": True,
    "application": False,
}
