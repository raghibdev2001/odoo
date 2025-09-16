from odoo import http
from odoo.http import request
import base64


class SlideAssignmentController(http.Controller):

    @http.route('/submit/assignment/<int:slide_id>', type='http', auth='user', methods=['POST'], csrf=False)
    def submit_assignment(self, slide_id, **post):
        Slide = request.env['slide.slide']
        slide = Slide.browse(slide_id)
        if not slide.exists():
            return request.not_found()

        file = post.get('file')
        if not file:
            print("File Not get")
            return request.redirect('/slides/slide/%d' % slide_id)

        request.env['slide.assignment.submission'].create({
            'name': file.filename,
            'slide_id': slide.id,
            'user_id': request.env.user.id,
            'file_data': base64.b64encode(file.read()),
            'filename': file.filename,
            # Optional: only include this if your model has it
            'assignment_id': slide.assignment_ids[0].id if slide.assignment_ids else False,
        })

        return request.redirect('/slides/slide/%d' % slide_id)