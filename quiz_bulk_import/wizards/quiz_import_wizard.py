from odoo import models, fields
import base64
import csv
import io

class QuizImportWizard(models.TransientModel):
    _name = 'quiz.import.wizard'
    _description = 'Quiz Bulk Import Wizard'

    upload_file = fields.Binary(string='Upload CSV File', required=True)
    file_name = fields.Char(string='Filename')

    def action_import_quizzes(self):
        decoded = base64.b64decode(self.upload_file)
        file_io = io.StringIO(decoded.decode('utf-8'))
        reader = csv.DictReader(file_io)

        for row in reader:
            course = self.env['slide.channel'].search([('name', '=', row['Course Name'])], limit=1)
            if not course:
                continue

            section = self.env['slide.slide'].search([
                ('name', '=', row['Section Title']),
                ('channel_id', '=', course.id),
            ], limit=1)

            if not section:
                section = self.env['slide.slide'].create({
                    'name': row['Section Title'],
                    'channel_id': course.id,
                    'slide_type': 'document',
                })

            quiz = self.env['slide.slide'].search([
                ('name', '=', row['Quiz Title']),
                ('channel_id', '=', course.id),
                ('slide_type', '=', 'quiz'),
            ], limit=1)

            if not quiz:
                quiz = self.env['slide.slide'].create({
                    'name': row['Quiz Title'],
                    'channel_id': course.id,
                    'slide_type': 'quiz',
                    'is_published': True,
                })

            question = self.env['slide.question'].create({
                'slide_id': quiz.id,
                'name': row['Question'],
                'question_type': 'multiple_choice',
            })

            for i in range(1, 4):
                ans_text = row.get(f'Answer {i}')
                is_correct = ans_text.strip().lower() == row['Correct Answer'].strip().lower()
                self.env['slide.answer'].create({
                    'question_id': question.id,
                    'text': ans_text,
                    'is_correct': is_correct,
                })
