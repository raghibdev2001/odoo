from odoo import http
from odoo.http import request
from odoo.addons.website_slides.controllers.main import WebsiteSlides

class WebsiteSlidesSequentialUnlock(WebsiteSlides):

    @http.route('/slides/slide/<model("slide.slide"):slide>', type='http', auth="public", website=True, sitemap=True)
    def slide_view(self, slide, **kwargs):
        print("Welcome here in overridden controller")

        if not slide.channel_id.can_access_from_current_website() or not slide.active:
            raise http.NotFound()

        if slide.is_category:
            return request.redirect(slide.channel_id.website_url)

        if slide.can_self_mark_completed and not slide.user_has_completed \
           and slide.channel_id.channel_type == 'training' and slide.slide_category != 'video':
            self._slide_mark_completed(slide)
            next_category_to_open = slide._get_next_category()
        else:
            self._set_viewed_slide(slide)
            next_category_to_open = False

        values = self._get_slide_detail(slide)

        if slide.question_ids:
            values.update(self._get_slide_quiz_data(slide))

        values['channel_progress'] = self._get_channel_progress(slide.channel_id, include_quiz=True)
        values['category_data'] = self._prepare_collapsed_categories(
            values['category_data'], slide, next_category_to_open
        )

        values.update({
            'search_category': slide.category_id if kwargs.get('search_category') else None,
            'search_tag': request.env['slide.tag'].browse(int(kwargs.get('search_tag'))) if kwargs.get('search_tag') else None,
            'slide_categories': dict(request.env['slide.slide']._fields['slide_category']._description_selection(request.env)) if kwargs.get('search_slide_category') else None,
            'search_slide_category': kwargs.get('search_slide_category'),
            'search_uncategorized': kwargs.get('search_uncategorized'),
        })

        values['channel'] = slide.channel_id
        values = self._prepare_additional_channel_values(values, **kwargs)
        values['signup_allowed'] = request.env['res.users'].sudo()._get_signup_invitation_scope() == 'b2c'

        if kwargs.get('fullscreen') == '1':
            print("Rendering fullscreen")

            # Inject your custom slide access map here
            slide_access_map = {}
            unlocked = True
            for slide_info in values.get('slides', []):
                slide_id = slide_info['id']
                completed = values['channel_progress'].get(slide_id, {}).get('completed', False)
                slide_access_map[slide_id] = unlocked
                if not completed:
                    unlocked = False

            values['slide_access_map'] = slide_access_map            
            return request.render("website_slides.slide_fullscreen", values)

        values.pop('channel', None)
        return request.render("website_slides.slide_main", values)
