# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class AuthOtpLog(models.Model):
    _name = 'auth.otp.log'
    _description = 'OTP Log'

    user_id = fields.Many2one('res.users', required=True, ondelete='cascade')
    otp = fields.Char(required=True)
    medium = fields.Selection([('email','Email'),('sms','SMS')], required=True)
    expiry = fields.Datetime(required=True)
    active = fields.Boolean(default=True)


    @api.model
    def cleanup_expired(self):
        now = fields.Datetime.now()
        expired = self.search([('expiry','<', now), ('active','=',True)])
        count = len(expired)
        if count:
            expired.write({'active': False})
            _logger.info("Deactivated %d expired OTP logs", count)
