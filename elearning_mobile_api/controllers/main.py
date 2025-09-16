
from odoo import http
from odoo.http import request, Response
import json
from ..utils.jwt_manager import generate_token, verify_token

def json_response(data, status=200):
    return Response(json.dumps(data), content_type='application/json', status=status)

class ElearningMobileAPI(http.Controller):

    @http.route('/api/signup', auth='public', type='json', csrf=False, methods=['POST'])
    def signup(self, **post):
        data = post
        if not all([data.get('name'), data.get('email'), data.get('password')]):
            return json_response({'error': 'Missing fields'}, 400)

        existing_user = request.env['res.users'].sudo().search([('login', '=', data['email'])])
        if existing_user:
            return json_response({'error': 'Email already registered'}, 400)

        user = request.env['res.users'].sudo().create({
            'name': data['name'],
            'login': data['email'],
            'email': data['email'],
            'password': data['password']
        })
        token = generate_token(user.id)
        return json_response({'token': token, 'user_id': user.id})

    @http.route('/api/signin', auth='public', type='json', csrf=False, methods=['POST'])
    def signin(self, **post):
        data = post
        user = request.env['res.users'].sudo().search([('login', '=', data['email'])], limit=1)
        if not user or not user._check_credentials(data['password']):
            return json_response({'error': 'Invalid credentials'}, 401)
        token = generate_token(user.id)
        return json_response({'token': token, 'user_id': user.id})

    @http.route('/api/courses', auth='public', methods=['GET'], csrf=False, type='http')
    def get_courses(self, **kwargs):
        token = request.httprequest.headers.get('Authorization')
        user_id = verify_token(token)
        if not user_id:
            return json_response({'error': 'Unauthorized'}, 401)

        courses = request.env['slide.channel'].sudo().search([])
        result = [{
            'id': course.id,
            'title': course.name,
            'description': course.description,
            'image': course.image_1920 and f'/web/image/slide.channel/{course.id}/image_1920' or None
        } for course in courses]
        return json_response({'courses': result})

    @http.route('/api/course/<int:course_id>', auth='public', methods=['GET'], csrf=False, type='http')
    def get_course_detail(self, course_id, **kwargs):
        token = request.httprequest.headers.get('Authorization')
        user_id = verify_token(token)
        if not user_id:
            return json_response({'error': 'Unauthorized'}, 401)

        course = request.env['slide.channel'].sudo().browse(course_id)
        if not course.exists():
            return json_response({'error': 'Course not found'}, 404)

        slides = course.slide_ids
        slide_data = [{'id': s.id, 'name': s.name, 'type': s.slide_type} for s in slides]
        return json_response({
            'id': course.id,
            'title': course.name,
            'description': course.description,
            'slides': slide_data
        })

    @http.route('/api/upload_assignment', auth='public', type='http', methods=['POST'], csrf=False)
    def upload_assignment(self, **kwargs):
        token = request.httprequest.headers.get('Authorization')
        user_id = verify_token(token)
        if not user_id:
            return json_response({'error': 'Unauthorized'}, 401)

        file = request.httprequest.files.get('assignment')
        slide_id = kwargs.get('slide_id')
        if not file or not slide_id:
            return json_response({'error': 'Missing assignment or slide_id'}, 400)

        attachment = request.env['ir.attachment'].sudo().create({
            'name': file.filename,
            'datas': file.read().encode('base64'),
            'res_model': 'slide.assignment.submission',
            'res_id': 0,
        })

        submission = request.env['slide.assignment.submission'].sudo().create({
            'user_id': user_id,
            'slide_id': int(slide_id),
            'attachment_id': attachment.id,
        })

        return json_response({'message': 'Assignment uploaded successfully', 'submission_id': submission.id})
