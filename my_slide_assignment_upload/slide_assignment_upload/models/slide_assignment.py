from odoo import models, fields, api

class SlideAssignment(models.Model):
    _name = 'slide.assignment'
    _description = 'Slide Assignment'

    name = fields.Char(string="Assignment Title")
    slide_id = fields.Many2one('slide.slide', string="Slide")
    user_id = fields.Many2one('res.users', string="Submitted By")
    submitted_date = fields.Datetime(string="Submitted On")
    attachment = fields.Binary(string="Uploaded File")
    filename = fields.Char(string="Filename")
    document = fields.Binary(string="Document")  # Required: binary file upload
    points = fields.Integer(string="Points")