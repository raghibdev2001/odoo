from odoo import http
from odoo.http import request, Response
import json
import base64
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

def decode_jwt(token):    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

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

    @http.route('/api/submit/assignment/<int:slide_id>', type='http', auth='public', methods=['POST'], csrf=False)
    @auth_required
    def api_submit_assignment(self, slide_id, **post):
        token = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
        payload = decode_jwt(token)

        if "error" in payload:
            return {"status": "error", "message": payload["error"]}

        user_id = payload.get("uid")
        if not user_id:
            return {"status": "error", "message": "Invalid token payload"}


        Slide = request.env['slide.slide']
        slide = Slide.browse(slide_id)
        if not slide.exists():
            return {"status": "error", "message": "Slide not found"}

        file = post.get('file')
        if not file:
            print("File Not get")
            return {"status": "error", "message": "File not found"}

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