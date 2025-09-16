# -*- coding: utf-8 -*-
import jwt
import logging
import json
from datetime import datetime, timedelta
from odoo import http
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo import http, SUPERUSER_ID

# # from twilio.rest import Client

_logger = logging.getLogger(__name__)
JWT_SECRET = 'YOUR_SECRET_KEY'
JWT_ALGO = 'HS256'

# # TWILIO_SID = 'TWILIO_ACCOUNT_SID'
# # TWILIO_TOKEN = 'TWILIO_AUTH_TOKEN'
# # TWILIO_FROM = 'YOUR_TWILIO_NUMBER'

# # twilio_client = Client(TWILIO_SID, TWILIO_TOKEN)

# # def send_sms(to, body):
# #     twilio_client.messages.create(to=to, from_=TWILIO_FROM, body=body)

def generate_otp():
    from random import randint
    return f"{randint(100000, 999999)}"

def encode_jwt(user):
    return jwt.encode({'uid': user.id, 'exp': datetime.utcnow() + timedelta(days=7)}, JWT_SECRET, algorithm=JWT_ALGO)

def auth_required(f):
    def wrap(*args, **kwargs):
        token = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            request.env.user = request.env['res.users'].browse(data['uid'])
        except Exception:
            return request.make_response('Unauthorized', 401)
        return f(*args, **kwargs)
    return wrap

def decode_jwt(token):    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return payload
    except jwt.ExpiredSignatureError:
        return {"error": "Token expired"}
    except jwt.InvalidTokenError:
        return {"error": "Invalid token"}

class AuthController(http.Controller):

    @http.route('/api/signup', type='json', auth='public', methods=['POST'], csrf=False)
    def api_signup(self, **kwargs):
        try:
            raw_data = request.httprequest.data.decode('utf-8')
            post = json.loads(raw_data)
        except Exception as e:
            return request.make_response(
                json.dumps({'error': 'Invalid JSON', 'details': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        required = ['first_name','last_name','username','email','password','confirm_password','phone']
        if any(not post.get(f) for f in required):
            return {'error': 'Missing fields'}

        if post['password'] != post['confirm_password']:
            return {'error': 'Passwords do not match'}

        existing = request.env['res.users'].sudo().search([('email', '=', post['email'])], limit=1)
        if existing:
            return {'error': 'Email already registered'}

        vals = {
            'name': f"{post['first_name']} {post['last_name']}",
            'login': post['username'],
            'email': post['email'],
            'phone': post['phone'],
            'password': post['password'],
            'groups_id': [(6, 0, [request.env.ref('base.group_portal').id])],
        }
        try:
            user = request.env['res.users'].with_user(SUPERUSER_ID).create(vals)

        except Exception as e:
            return {"status": "error", "message": str(e)}
        
        email = post.get('email'); 
        if not email:
            return {'error': 'Email required'}
        user = request.env['res.users'].sudo().search([('email','=', email)], limit=1)
        if not user:
            return {'error': 'Unknown email'}
            
        otp = generate_otp()
        expiry = datetime.utcnow() + timedelta(minutes=10)

        log_vals = {
            'user_id': user.id,
            'otp': otp,
            'medium': 'email',
            'expiry': expiry,
        }
        email_log = request.env['auth.otp.log'].sudo().create(log_vals)

        # Send OTP Email
        try:
            template = request.env.ref('odoo_elearning_auth.template_auth_otp')
            if template:
                template.sudo().send_mail(
                    email_log.id,
                    force_send=True,
                    email_values={'email_to': email}
                )
                _logger.info("OTP email sent to %s", user.email)
                _logger.info("Created user %s and sent OTP", user.email)
                
                # Create OTP log (sms placeholder)
                # sms_log = request.env['auth.otp.log'].sudo().create({
                #     'user_id': user.id,
                #     'otp': otp,
                #     'medium': 'sms',
                #     'expiry': expiry
                # })
                # send_sms(user.phone, f"Your OTP code is {otp}")   # implement later
		
                return {'status': 'success', 'message': otp}
            
            else:
                _logger.error("OTP email template not found!")
                return {'status': 'success', 'message': "User created but OTP email template missing."}
        except Exception as e:
            _logger.error("Failed to send OTP email: %s", str(e))
            return {"status": "error", "message": "User created but OTP email failed."}

        # sms_log = request.env['auth.otp.log'].sudo().create(dict(log_vals, medium='sms'))
        # send_sms(user.phone, f"Your OTP code is {otp}")        
    

    @http.route('/api/verify_user', type='json', auth='public', methods=['POST'], csrf=False)
    def verify(self, **kwargs):
        try:
            raw_data = request.httprequest.data.decode('utf-8')
            post = json.loads(raw_data)
        except Exception as e:
            return request.make_response(
                json.dumps({'error': 'Invalid JSON', 'details': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        email = post.get('email'); otp = post.get('otp')
        if not email or not otp:
            return {'error': 'Email and OTP required'}

        user = request.env['res.users'].sudo().search([('email','=',email)], limit=1)
        if not user:
            return {'error': 'Unknown email'}

        now = datetime.utcnow()
        logs = request.env['auth.otp.log'].sudo().search([
            ('user_id','=',user.id),
            ('otp','=', otp),
            ('active','=',True),
            ('expiry','>=', now),
        ], limit=1)

        if not logs:
            return {'error': 'Invalid or expired OTP'}

        logs.sudo().write({'active': False})
        token = encode_jwt(user)
        # Build user data
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.login,
            "phone": user.partner_id.phone,
            "mobile": user.partner_id.mobile,
            "company": user.company_id.name if user.company_id else None,
            "lang": user.lang,
            "timezone": user.tz,
        }

        return {
            "token": token,
            "user": user_data
        }
    

    @http.route('/api/login', type='json', auth='public', methods=['POST'], csrf=False)
    def login(self, **kwargs):
        try:
            raw_data = request.httprequest.data.decode('utf-8')
            post = json.loads(raw_data)
        except Exception as e:
            return request.make_response(
                json.dumps({'error': 'Invalid JSON', 'details': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        
        login_email = post.get('email'); login_password = post.get('password')

        user = request.env['res.users'].sudo().search([('login', '=', login_email)], limit=1)
        if not user:
            return {"error": "User not found"}
        elif not user.active:
            return {"error": "User is inactive"}

        try:
            uid = request.session.authenticate(request.env.cr.dbname, login_email, login_password)
            if not uid:
                return {"status": "fail", "message": "Invalid credentials"}
        except AccessDenied:
            return {"status": "fail", "message": "Access Denied: Incorrect email or password"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


        user = request.env['res.users'].sudo().browse(uid)

        # JWT Token
        token = encode_jwt(user)

        # Build user data
        user_data = {
            "id": user.id,
            "name": user.name,
            "email": user.login,
            "phone": user.partner_id.phone,
            "mobile": user.partner_id.mobile,
            "company": user.company_id.name if user.company_id else None,
            "lang": user.lang,
            "timezone": user.tz,
        }


        # -------------------------------
        # eLearning Analytics (Courses)
        # -------------------------------
        analytics = []
        course_partners = request.env['slide.channel.partner'].sudo().search([
            ('partner_id', '=', user.partner_id.id)
        ])

        SlidePartner = request.env['slide.slide.partner'].sudo()

        for cp in course_partners:
            # Compute rank based on XP (descending order)
            partners = request.env['slide.channel.partner'].sudo().search(
                [('channel_id', '=', cp.channel_id.id)], 
                order="xp desc"
            )
            rank = 1
            for p in partners:
                if p.partner_id.id == user.partner_id.id:
                    break
                rank += 1

            # Slides
            total_slides = len(cp.channel_id.slide_ids)
            completed_slides = SlidePartner.search_count([
                ('partner_id', '=', user.partner_id.id),
                ('channel_id', '=', cp.channel_id.id),
                ('completed', '=', True)
            ])

            analytics.append({
                "course_id": cp.channel_id.id,
                "course_name": cp.channel_id.name,
                "enrolled_date": cp.create_date.strftime("%Y-%m-%d %H:%M:%S"),
                "progress": cp.completion,   # percentage
                "xp": cp.xp,
                "completed": True if cp.completion == 100 else False,
                "rank": rank,
                "total_slides": total_slides,
                "completed_slides": completed_slides,
            })

        return {
            "token": token,
            "user": user_data,
            "analytics": analytics
        }
    

    @http.route('/api/forgotPassword', type='json', auth='public', methods=['POST'], csrf=False)
    def forgot_password(self, **kwargs):
        try:
            raw_data = request.httprequest.data.decode('utf-8')
            post = json.loads(raw_data)
        except Exception as e:
            return request.make_response(
                json.dumps({'error': 'Invalid JSON', 'details': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        
        email = post.get('email'); 
        if not email:
            return {'error': 'Email required'}
        user = request.env['res.users'].sudo().search([('email','=', email)], limit=1)
        if not user:
            return {'error': 'Unknown email'}

        otp = generate_otp()
        expiry = datetime.utcnow() + timedelta(minutes=10)

        # Create OTP log (email)
        email_log = request.env['auth.otp.log'].sudo().create({
            'user_id': user.id,
            'otp': otp,
            'medium': 'email',
            'expiry': expiry
        })

        # Send email using template, overriding recipient
        template = request.env.ref('odoo_elearning_auth.template_auth_otp')
        template.sudo().send_mail(
            email_log.id,
            force_send=True,
            email_values={'email_to': email}
        )
        _logger.info("OTP email sent to %s", user.email)
        _logger.info("Created user %s and sent OTP", user.email)
        _logger.info(template)

        # Create OTP log (sms placeholder)
        # sms_log = request.env['auth.otp.log'].sudo().create({
        #     'user_id': user.id,
        #     'otp': otp,
        #     'medium': 'sms',
        #     'expiry': expiry
        # })
        # send_sms(user.phone, f"Your OTP code is {otp}")   # implement later

        return {'success': True, 'message': 'OTP sent successfully'}

    @http.route('/api/resetPassword', type='json', auth='public', methods=['POST'], csrf=False)
    def reset_password(self, **kwargs):
        try:
            raw_data = request.httprequest.data.decode('utf-8')
            post = json.loads(raw_data)
        except Exception as e:
            return request.make_response(
                json.dumps({'error': 'Invalid JSON', 'details': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )

        email=post.get('email'); otp=post.get('otp'); password=post.get('password'); confirm_password=post.get('confirm_password');

        if password != confirm_password:
            return {'error': 'Passwords do not match'}
        user = request.env['res.users'].sudo().search([('email','=',email)], limit=1)
        if not user:
            return {'error': 'Unknown email'}
        now = datetime.utcnow()
        logs = request.env['auth.otp.log'].sudo().search([('user_id','=',user.id),('otp','=',otp),('expiry','>=',now),('active','=',True)], limit=1)
        if not logs:
            return {'error': 'Invalid or expired OTP'}
        logs.sudo().write({'active': False})
        user.sudo().write({'password': password})
        return {'success': True}
    


    @http.route('/api/me', type='json', auth='public', methods=['POST'], csrf=False)
    def me(self, **kwargs):
        """Return user info from Bearer JWT token"""
        try:
            token = request.httprequest.headers.get('Authorization', '').replace('Bearer ', '')
            payload = decode_jwt(token)

            if "error" in payload:
                return {"status": "fail", "message": payload["error"]}

            user_id = payload.get("uid")
            if not user_id:
                return {"status": "fail", "message": "Invalid token payload"}

            user = request.env['res.users'].sudo().browse(user_id)
            if not user.exists() or not user.active:
                return {"status": "fail", "message": "User not found or inactive"}

            # Build user data
            user_data = {
                "id": user.id,
                "name": user.name,
                "email": user.login,
                "phone": user.partner_id.phone,
                "mobile": user.partner_id.mobile,
                "company": user.company_id.name if user.company_id else None,
                "lang": user.lang,
                "timezone": user.tz,
            }

        # -------------------------------
            # eLearning Analytics (Courses)
            # -------------------------------
            analytics = []
            course_partners = request.env['slide.channel.partner'].sudo().search([
                ('partner_id', '=', user.partner_id.id)
            ])

            SlidePartner = request.env['slide.slide.partner'].sudo()

            for cp in course_partners:
                # Compute rank in this course based on XP
                partners = request.env['slide.channel.partner'].sudo().search(
                    [('channel_id', '=', cp.channel_id.id)],
                    order="xp desc"
                )
                rank = 1
                for p in partners:
                    if p.partner_id.id == user.partner_id.id:
                        break
                    rank += 1

                # Slides completion stats
                total_slides = len(cp.channel_id.slide_ids)
                completed_slides = SlidePartner.search_count([
                    ('partner_id', '=', user.partner_id.id),
                    ('channel_id', '=', cp.channel_id.id),
                    ('completed', '=', True)
                ])

                analytics.append({
                    "course_id": cp.channel_id.id,
                    "course_name": cp.channel_id.name,
                    "enrolled_date": cp.create_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "progress": cp.completion,   # percentage
                    "xp": cp.xp,
                    "completed": (cp.completion == 100),
                    "rank": rank,
                    "total_slides": total_slides,
                    "completed_slides": completed_slides,
                })

            # -------------------------------
            # Response
            # -------------------------------
            return {
                "status": "success",
                "token": token,
                "user": user_data,
                "analytics": analytics
            }

        except Exception as e:
            return {"status": "error", "message": str(e)}