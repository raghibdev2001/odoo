from odoo import models, fields, api

class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    assignment_ids = fields.One2many('slide.assignment', 'slide_id', string='Assignments')
    assignment_submission_ids = fields.One2many('slide.assignment.submission', 'slide_id', string='User Submissions')

    @property
    def total_assignment_xp(self):
        self.ensure_one()
        submissions = self.env['slide.assignment.submission'].search([
            ('slide_id', '=', self.id),
            ('user_id', '=', self.env.uid)
        ])
        return sum(sub.points or 0 for sub in submissions)