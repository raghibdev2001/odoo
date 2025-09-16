import base64
import csv
from io import StringIO
from odoo import models, fields

class QuizImportWizard(models.TransientModel):
    _name = 'quiz.import.wizard'
    _description = 'Import Quizzes'

    upload_file = fields.Binary(string="Upload File", required=True)
    file_name = fields.Char("File Name")

    def _resequence_slides(self, channel_id, section_id, after_sequence):
        """ Ensure proper sequencing of slides after insertion """
        slides = self.env['slide.slide'].search([
            ('channel_id', '=', channel_id),
            ('sequence', '>', after_sequence),
            ('id', '!=', section_id)
        ], order='sequence')
        
        sequence = after_sequence + 1
        for slide in slides:
            slide.write({'sequence': sequence})
            sequence += 1

    def action_import(self):
        data = base64.b64decode(self.upload_file)
        file_str = data.decode('utf-8')
        csv_reader = csv.DictReader(StringIO(file_str))

        for row in csv_reader:
            course = self.env['slide.channel'].search([('name', '=', row['Course Name'])], limit=1)
            print(row['Course Name'])
            if not course:
                print("course not found")
                continue

            ##### Section Finding, if not then create
            section = self.env['slide.slide'].search([
                ('name', '=', row['Section Title']),
                ('channel_id', '=', course.id),
                ('is_category', '=', True),
            ], limit=1)

            print("Section")
            print(row['Section Title'])
            print(section.id)

            if not section:
                self.env.cr.commit()
                print("section not found")
                section = self.env['slide.slide'].create({
                    'name': row['Section Title'],
                    'channel_id': course.id,
                    'slide_type': 'document',
                    'is_section': True,
                    'sequence': 0,
                })

            course_id = ''
            section_id = ''
            course_id = course.id
            section_id = section.id

            # Get the next sequence number after the section
            category_last_sequence = self.env['slide.slide'].search([
                ('category_id', '=', section_id),
            ], order='sequence desc', limit=1)
            next_sequence = category_last_sequence.sequence
            
            ##### Quiz Finding, if not then create
            quiz = self.env['slide.slide'].search([
                ('name', '=', row['Quiz Title']),
                ('channel_id', '=', course.id),
                ('slide_type', '=', 'quiz'),
            ], limit=1)

            print("quiz")
            print(row['Quiz Title'])
            print(quiz.id)

            if not quiz:
                print("quiz not found")
                print("Final section ID used for quiz:", section_id, section.name)
                quiz = self.env['slide.slide'].create({
                    'name': row['Quiz Title'],
                    'channel_id': course_id,
                    'category_id': section_id,
                    'slide_type': 'quiz',
                    'slide_category': 'quiz',
                    'is_published': True,
                    'sequence': next_sequence,
                })

                # After creating, we might need to re-sequence other slides
                self._resequence_slides(course_id, section_id, next_sequence)
          
            ##### Question Finding, if not then create
            question = self.env['slide.question'].create({
                'slide_id': quiz.id,
                'question': row['Question']
                #'question_type': 'multiple_choice',
            })

            for i in range(1, 4):
                ans_text = row.get(f'Answer {i}')
                is_correct = ans_text.strip().lower() == row['Correct Answer'].strip().lower()
                self.env['slide.answer'].create({
                    'question_id': question.id,
                    'text_value': ans_text,
                    'is_correct': is_correct,
                })
            
            print(" ")
            print(" ")
            # self.env['quiz.quiz'].create({
            #     'name': row['Quiz Name'],
            #     'question': row['Question'],
            #     'section_id': section.id
            # })

            # # Process answers
            # for i in range(1, 6):  # Support 5 answers max
            #     answer_text = row.get(f'Answer {i}')
            #     correct_flag = row.get(f'Correct {i}')
            #     if answer_text:
            #         self.env['quiz.answer'].create({
            #             'name': answer_text,
            #             'is_correct': correct_flag.lower() == 'true',
            #             'quiz_id': quiz.id
            #         })