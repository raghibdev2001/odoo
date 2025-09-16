from odoo import models, fields


class SlideChannel(models.Model):
    _inherit = 'slide.channel'

    section_ids = fields.One2many('course.section', 'course_id', string="Sections")

class CourseSection(models.Model):
    _name = 'course.section'
    _description = 'Course Section'

    name = fields.Char()
    #course_id = fields.Many2one('course.course', required=True)
    course_id = fields.Many2one('slide.channel', required=True)  # Fix here
    quiz_ids = fields.One2many('quiz.quiz', 'section_id')

class Quiz(models.Model):
    _name = 'quiz.quiz'
    _description = 'Quiz'

    name = fields.Char(required=True)
    section_id = fields.Many2one('course.section', required=True)
    question = fields.Text()
    answer_ids = fields.One2many('quiz.answer', 'quiz_id')

    # _name = 'quiz.quiz'
    # _description = 'Quiz'

    # name = fields.Char(required=True)
    # section_id = fields.Many2one('course.section', required=True)
    # question = fields.Text()


class QuizAnswer(models.Model):
    _name = 'quiz.answer'
    _description = 'Quiz Answer Option'

    name = fields.Char(required=True)
    is_correct = fields.Boolean(default=False)
    quiz_id = fields.Many2one('quiz.quiz', required=True)

