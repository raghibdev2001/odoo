from odoo import models, fields, api

class SlideAssignmentSubmission(models.Model):
    _name = 'slide.assignment.submission'
    _description = 'Slide Assignment Submission'

    name = fields.Char(string="Assignment Title")
    slide_id = fields.Many2one('slide.slide', required=True)
    assignment_id = fields.Many2one('slide.assignment', string="Assignment")
    user_id = fields.Many2one('res.users', required=True)
    user_email = fields.Char(string="User Email", compute="_compute_user_email", store=True)
    submitted_date = fields.Datetime()
    filename = fields.Char()
    file_data = fields.Binary(string='Assignment File')
    document = fields.Binary(string="Document")
    points = fields.Integer(string="Points")

    @api.depends('user_id')
    def _compute_user_email(self):
        for rec in self:
            rec.user_email = rec.user_id.email or ""

    @api.model
    def create(self, vals):
        vals['submitted_date'] = datetime.now()
        return super().create(vals)

    def write(self, vals):
        res = super().write(vals)

        if 'points' in vals:
            for submission in self:
                if submission.points and submission.user_id and submission.slide_id:
                    # Get course (channel) and user partner
                    channel = submission.slide_id.channel_id
                    partner = submission.user_id.partner_id

                    if channel and partner:
                        # Find existing channel-partner record
                        channel_partner = self.env['slide.channel.partner'].sudo().search([
                            ('channel_id', '=', channel.id),
                            ('partner_id', '=', partner.id)
                        ], limit=1)

                        if channel_partner:
                            # Add points to existing XP
                            new_xp = (channel_partner.xp or 0) + submission.points
                            channel_partner.sudo().write({'xp': new_xp})

        return res