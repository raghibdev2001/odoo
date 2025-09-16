from odoo import models, fields, api

class SlideAssignment(models.Model):
    _name = "slide.assignment"
    _description = "Slide Assignment"

    submitted_date = fields.Datetime(string='Submitted Date')
    slide_id = fields.Many2one("slide.slide", required=True, string="Slide")
    user_id = fields.Many2one("res.users", required=True, string="User")
    document = fields.Binary(string="Assignment Document", required=True)
    filename = fields.Char(string="Filename")
    points = fields.Integer(string="Points", default=0)
    submitted = fields.Boolean(string="Submitted", default=True)
