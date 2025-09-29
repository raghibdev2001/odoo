# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
import jwt
import json
import base64
from functools import wraps
import logging
from odoo import http, SUPERUSER_ID

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

def decode_jwt(token):    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

class CourseController(http.Controller):

    @http.route('/api/courses', type='json', auth='public', methods=['POST'], csrf=False)
    @auth_required
    def get_courses(self, **kwargs):

        token = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
        payload = decode_jwt(token)

        if "error" in payload:
            return {"status": "fail", "message": payload["error"]}

        user_id = payload.get("uid")
        if not user_id:
            return {"status": "fail", "message": "Invalid token payload"}

        user = request.env['res.users'].sudo().browse(user_id)

        params = request.httprequest.args  # use query string params
        domain = [('is_published', '=', True)]

        if params.get('category_id'):
            domain.append(('category_id', '=', int(params.get('category_id'))))
        if params.get('tag_id'):
            domain.append(('tag_ids', 'in', [int(params.get('tag_id'))]))
        if params.get('search'):
            domain.append(('name', 'ilike', params.get('search')))

        # Courses assigned to user
        course_ids = request.env['slide.channel.partner'].sudo().search([
            ('partner_id', '=', user.partner_id.id)
        ]).mapped("channel_id.id")

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
                'assigned': 1 if course.id in course_ids else 0,
                'price': course.product_id.list_price if course.product_id else 0.0,
                'currency': {
                    "id": course.product_id.currency_id.id if course.product_id else None,
                    "name": course.product_id.currency_id.name if course.product_id else '',
                    "symbol": course.product_id.currency_id.symbol if course.product_id else ''
                },
            })


        return {"status": "success", "data": result}
    
    @http.route('/api/course/<int:course_id>', type='json', auth='public', methods=['POST'], csrf=False)
    @auth_required
    def get_course_detail(self, course_id, **kwargs):
        course = request.env['slide.channel'].sudo().browse(course_id)
        if not course or not course.exists():
            return {"status": "error", "message": "Course not found"}

        slides = []
        for slide in course.slide_ids.filtered(lambda s: s.is_published):
            slide_data = {
                'id': slide.id,
                'name': slide.name,
                'type': slide.slide_type,
                'url': slide.url,
                'sequence': slide.sequence,
                'is_quiz': slide.slide_type == 'quiz',
                'is_section': slide.is_category,
                'category_id': slide.category_id.id if slide.category_id else None,
            }

            # If it's a quiz, include questions & answers
            if slide.slide_type == 'quiz':
                questions = []
                for q in slide.question_ids:
                    answers = []
                    for ans in q.answer_ids:
                        answers.append({
                            'id': ans.id,
                            'text': ans.text_value or '',
                            'correct': ans.is_correct or 0
                        })
                    questions.append({
                        'id': q.id,
                        'question': q.question,
                        'answers': answers,                        
                    })
                slide_data['questions'] = questions

            slides.append(slide_data)

        return {
            "status": "success",
            "data": {
                "id": course.id,
                "name": course.name,
                "description": course.description or '',
                "image_url": course.image_1920 and f'/web/image/slide.channel/{course.id}/image_1920',
                #"category": course.category_id.name if course.category_id else '',
                'price': course.product_id.list_price if course.product_id else 0.0,
                'currency': {
                    "id": course.product_id.currency_id.id if course.product_id else None,
                    "name": course.product_id.currency_id.name if course.product_id else '',
                    "symbol": course.product_id.currency_id.symbol if course.product_id else ''
                },
                "slides": slides,
            }
        }

    @http.route('/api/quiz/submit', type='json', auth='user', methods=['POST'], csrf=False)
    def submit_quiz(self, **kwargs):
        try:
            data = request.httprequest.data.decode('utf-8')   # <-- this gives you the JSON body
            post = json.loads(data)
            slide_id = post['slide_id']
            answers = post['answers']
            

            if not slide_id or not answers:
                return {"status": "error", "message": "Missing parameters"}

            slide = request.env['slide.slide'].sudo().browse(slide_id)
            if not slide or slide.slide_type != 'quiz':
                return {"status": "error", "message": "Invalid quiz"}

            result_data = []
            score = 0
            for ans in answers:
                q = request.env['slide.question'].sudo().browse(ans['question_id'])
                correct_answer_ids = q.answer_ids.filtered(lambda a: a.is_correct).ids
                user_answer_ids = ans['answer_ids']

                is_correct = set(user_answer_ids) == set(correct_answer_ids)
                if is_correct:
                    score += 1

                result_data.append({
                    "question_id": q.id,
                    "question": q.question,
                    "user_answer_ids": user_answer_ids,
                    "correct_answer_ids": correct_answer_ids,
                    "is_correct": is_correct,
                })

            return {
                "status": "success",
                "quiz_id": slide.id,
                "total_questions": len(slide.question_ids),
                "score": score,
                "results": result_data,
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}


    @http.route('/api/upload/assignment/<int:slide_id>', type='http', auth='public', methods=['POST'], csrf=False)
    @auth_required
    def api_submit_assignment(self, slide_id, **post):
        try:
            token = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
            payload = decode_jwt(token)

            if "error" in payload:
                resulterr =  {"status": "error", "message": payload["error"]}
                return Response(
                    json.dumps(resulterr),
                    content_type="application/json",
                    status=200
                )

            user_id = payload.get("uid")
            if not user_id:
                resulterr =  {"status": "error", "message": "Invalid token payload"}
                return Response(
                    json.dumps(resulterr),
                    content_type="application/json",
                    status=200
                )


            Slide = request.env['slide.slide']
            slide = Slide.browse(slide_id)
            if not slide.exists():
                resulterr =  {"status": "error", "message": "Slide not found"}
                return Response(
                    json.dumps(resulterr),
                    content_type="application/json",
                    status=200
                )

            file = post.get('file')
            if not file:
                print("File Not get")
                resulterr =  {"status": "error", "message": "File not found"}
                return Response(
                    json.dumps(resulterr),
                    content_type="application/json",
                    status=200
                )

            request.env['slide.assignment.submission'].create({
                'name': file.filename,
                'slide_id': slide.id,
                'user_id': request.env.user.id,
                'file_data': base64.b64encode(file.read()),
                'filename': file.filename,
                # Optional: only include this if your model has it
                'assignment_id': slide.assignment_ids[0].id if slide.assignment_ids else False,
            })

            result = {
                "status": "success",
                "data": {
                    "slide_id": slide.id,
                    "name": file.filename,
                    "user_id": request.env.user.id,
                    "filename": file.filename,
                }
            }
            return Response(
                json.dumps(result),
                content_type="application/json",
                status=200
            )
        except Exception as e:
            return {"status": "error", "message": str(e)}