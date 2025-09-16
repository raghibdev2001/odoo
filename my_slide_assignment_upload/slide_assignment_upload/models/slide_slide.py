from odoo import models, fields

class SlideSlide(models.Model):
    _inherit = 'slide.slide'

    assignment_ids = fields.One2many('slide.assignment', 'slide_id', string='Assignments')
    assignment_submission_ids = fields.One2many('slide.assignment.submission', 'slide_id', string='User Submissions')

    def update_xp_on_assignment(self, slide_id, user_id, xp):
        slide_partner = self.env['slide.slide.partner'].sudo().search([
            ('slide_id', '=', slide_id),
            ('partner_id', '=', self.env['res.users'].browse(user_id).partner_id.id)
        ], limit=1)

        if not slide_partner:
            # Create it if doesn't exist
            slide_partner = self.env['slide.slide.partner'].sudo().create({
                'slide_id': slide_id,
                'partner_id': self.env['res.users'].browse(user_id).partner_id.id,
                'completed': True,
                'completion_date': fields.Datetime.now(),
                'xp': xp
            })
        else:
            slide_partner.sudo().write({
                'xp': xp,
                'completed': True,
                'completion_date': fields.Datetime.now()
            })
