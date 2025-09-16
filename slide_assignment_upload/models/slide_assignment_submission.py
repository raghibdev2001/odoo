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
    karma = fields.Char(string="Total Curent XP", compute="_compute_user_karma", store=True)

    @api.depends('user_id')
    def _compute_user_email(self):
        for rec in self:
            rec.user_email = rec.user_id.email or ""

    @api.depends('user_id')
    def _compute_user_karma(self):
        for rec in self:
            rec.karma = rec.user_id.karma or ""

    def write(self, vals):
        res = super().write(vals)

        if 'points' in vals:
            for submission in self:
                if submission.points and submission.user_id and submission.slide_id:
                    # Find related channel (course) and partner (user)
                    channel = submission.slide_id.channel_id
                    partner = submission.user_id.partner_id

                    if channel and partner:
                        # Get slide.channel.partner record
                        channel_partner = self.env['slide.channel.partner'].sudo().search([
                            ('channel_id', '=', channel.id),
                            ('partner_id', '=', partner.id)
                        ], limit=1)

                        if channel_partner:

                            # Old Number
                            old_channel_partner_value = channel_partner.xp

                            # Recalculate total points from all submissions for this user in this course
                            total_points = sum(self.env['slide.assignment.submission'].sudo().search([
                                ('slide_id.channel_id', '=', channel.id),
                                ('user_id', '=', submission.user_id.id)
                            ]).mapped('points'))

                            # Fetch quiz XP from gamification.karma.tracking table
                            karma_record = self.env['gamification.karma.tracking'].sudo().search([
                                ('user_id', '=', submission.user_id.id)
                            ], order="id desc", limit=1)

                            karma_record_quiz_xp = karma_record.new_value if karma_record else 0

                            # Update combined XP
                            channel_partner.sudo().write({'xp': total_points})

                            channel_partner_diff_value = abs(old_channel_partner_value - total_points)

                            # If old channel partner value is greater than the current sum point than it must be subtract from karma
                            if old_channel_partner_value > total_points:
                                # update res_users karma field
                                submission.user_id.sudo().write({'karma': karma_record_quiz_xp - channel_partner_diff_value })  
                            else:                                
                                # update res_users karma field
                                submission.user_id.sudo().write({'karma': karma_record_quiz_xp + channel_partner_diff_value })

        return res