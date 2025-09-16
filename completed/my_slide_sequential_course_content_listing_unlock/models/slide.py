from odoo import models, fields

class Slide(models.Model):
    _inherit = 'slide.slide'

    is_unlocked = fields.Boolean(compute='_compute_is_unlocked', store=False)

    def _compute_is_unlocked(self):
        user = self.env.user
        for slide in self:
            slide.is_unlocked = slide._is_slide_unlocked(user)

    def _is_slide_unlocked(self, user=None):
        self.ensure_one()
        user = user or self.env.user

        if user._is_public():
            return False

        slides = self.env['slide.slide'].search(
            [('channel_id', '=', self.channel_id.id)],
            order='category_id, sequence, id'
        )

        slide_list = list(slides)
        first_slide = slide_list[0] if slide_list else self
        if self == first_slide:
            return True

        try:
            current_index = slide_list.index(self)
        except ValueError:
            return False

        previous_slides = slide_list[:current_index]
        completed_ids = self.env['slide.slide.partner'].search([
            ('slide_id', 'in', [s.id for s in previous_slides]),
            ('partner_id', '=', user.partner_id.id),
            ('completed', '=', True)
        ]).mapped('slide_id').ids

        return all(s.id in completed_ids for s in previous_slides)
