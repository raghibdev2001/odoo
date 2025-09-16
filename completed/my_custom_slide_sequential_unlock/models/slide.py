from odoo import models, fields, api

class Slide(models.Model):
    _inherit = 'slide.slide'

    def _check_previous_slide_completed_2(self, user=None):
        """Allow viewing only if previous slides are completed, first section's first course always allowed."""
        self.ensure_one()
        user = user or self.env.user

        # Explicitly block public user
        if user._is_public():
            return False

        # 1. Get all slides in the course (ordered properly: section, sequence, id)
        Slide = self.env['slide.slide']

        all_slides = Slide.search(
            [('channel_id', '=', self.channel_id.id)],
            order='category_id, sequence, id'
        )

        if not all_slides:
            return True  # No slides, allow by default

        slide_list = list(all_slides)

        # 2. Identify the FIRST SLIDE (First Section, First Content)
        first_slide = slide_list[0]

        if self == first_slide:
            return True  # Always allow first slide of first section

        # 3. Find the index of the current slide
        try:
            current_index = slide_list.index(self)
        except ValueError:
            return False  # Slide not found in list, don't allow access

        # 4. Check if ALL previous slides (before current slide) are completed
        previous_slides = slide_list[:current_index]

        SlidePartner = self.env['slide.slide.partner']
        completed_slide_ids = SlidePartner.search([
            ('slide_id', 'in', [slide.id for slide in previous_slides]),
            ('partner_id', '=', user.partner_id.id),
            ('completed', '=', True)
        ]).mapped('slide_id')

        for prev_slide in previous_slides:
            if prev_slide.id not in completed_slide_ids.ids:
                return False  # Block access if any previous slide is not completed

        return True


    def _get_accessible_slide(self):
        """Only allow access to slide if previous slides are completed"""
        accessible_slides = []
        user = self.env.user
        for slide in self:
            if slide._check_previous_slide_completed(user):
                accessible_slides.append(slide.id)
        return accessible_slides