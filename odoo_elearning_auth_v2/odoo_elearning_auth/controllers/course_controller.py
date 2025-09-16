# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import jwt
from functools import wraps
import logging

_logger = logging.getLogger(__name__)
JWT_SECRET = 'YOUR_SECRET_KEY'
JWT_ALGO = 'HS256'

def auth_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            request.env.user = request.env['res.users'].sudo().browse(payload['uid'])
        except Exception as e:
            return Response("Unauthorized", status=401)
        return func(*args, **kwargs)
    return wrapper

class CourseController(http.Controller):

    @http.route('/api/courses', type='json', auth='public', methods=['GET'], csrf=False)
    @auth_required
    def get_courses(self, **kwargs):
        params = request.httprequest.args  # use query string params
        domain = [('is_published', '=', True)]

        if params.get('category_id'):
            domain.append(('category_id', '=', int(params.get('category_id'))))
        if params.get('tag_id'):
            domain.append(('tag_ids', 'in', [int(params.get('tag_id'))]))
        if params.get('search'):
            domain.append(('name', 'ilike', params.get('search')))

        courses = request.env['slide.channel'].sudo().search(domain)
        result = []

        for course in courses:
            result.append({
                'id': course.id,
                'name': course.name,
                'description': course.description or '',
                'image_url': course.image_1920 and f'/web/image/slide.channel/{course.id}/image_1920',
                'tags': [t.name for t in course.tag_ids],
                'type': course.channel_type,
                'published': course.is_published,
            })

        return {"status": "success", "data": result}

    @http.route('/api/course/<int:course_id>', type='json', auth='public', methods=['GET'], csrf=False)
    @auth_required
    def get_course_detail(self, course_id, **kwargs):
        course = request.env['slide.channel'].sudo().browse(course_id)
        if not course or not course.exists():
            return {"status": "error", "message": "Course not found"}

        slides = []
        for slide in course.slide_ids.filtered(lambda s: s.is_published):
            slides.append({
                'id': slide.id,
                'name': slide.name,
                'type': slide.slide_type,
                'url': slide.url,
                'sequence': slide.sequence,
                'is_quiz': slide.slide_type == 'quiz',
                'quiz_question_count': len(slide.question_ids) if slide.slide_type == 'quiz' else 0,
            })

        return {
            "status": "success",
            "data": {
                "id": course.id,
                "name": course.name,
                "description": course.description or '',
                "image_url": course.image_1920 and f'/web/image/slide.channel/{course.id}/image_1920',
                #"category": course.category_id.name if course.category_id else '',
                "slides": slides,
            }
        }