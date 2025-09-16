from odoo import models, fields

class SlideChannelPartner(models.Model):
    _inherit = 'slide.channel.partner'

    xp = fields.Integer(string="XP", default=0)
