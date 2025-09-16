from odoo import models

class Slide(models.Model):
    _inherit = 'slide.slide'

    def get_total_xp_for_user(self, user_id):
        self.ensure_one()
        total_xp = 0

        # Get XP from slide_channel_partner (quiz/completion)
        partner = self.env['res.users'].browse(user_id).partner_id
        scp = self.env['slide.channel.partner'].search([
            ('slide_id', '=', self.id),
            ('partner_id', '=', partner.id)
        ], limit=1)

        if scp:
            total_xp += scp.quiz_score or scp.xp or 0

        # Get assignment XP
        assignment = self.env['slide.assignment.submission'].search([
            ('slide_id', '=', self.id),
            ('user_id', '=', user_id)
        ], limit=1)
        if assignment:
            total_xp += assignment.points or 0

        return total_xp
