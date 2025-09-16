# -*- coding:utf-8 -*-

from odoo import api, models
from translatepy import Translator
from convertdate import islamic

# Define Islamic month names in Urdu
ISLAMIC_MONTH_NAMES_URDU = [
    "محرم", "صفر", "ربیع الاول", "ربیع الثانی",
    "جمادی الاول", "جمادی الثانی", "رجب", "شعبان",
    "رمضان", "شوال", "ذو القعدہ", "ذو الحجہ"
]

class PayslipDetailsReport(models.AbstractModel):
    _name = 'report.hr_payroll_community.report_payslip_details_urdu'
    _description = 'Payslip Details Urdu Report'



    # Function to translate fields with error handling
    def translate_field(self, translator, text, language="Urdu"):
        try:
            return translator.translate(text, language)
        except Exception as e:
            print(f"Translation failed for '{text}': {e}")
            return text  # Return original text if translation fails


    def gregorian_to_islamic_in_urdu(self, date):

        islamic_date = islamic.from_gregorian(date.year, date.month, date.day)
        month_name = ISLAMIC_MONTH_NAMES_URDU[islamic_date[1] - 1]
        formatted_date = f"{islamic_date[2]} {month_name} {islamic_date[0]} ہجری"
        formatted_date = formatted_date + "."
        return formatted_date

    def get_details_by_rule_category(self, payslip_lines):
        PayslipLine = self.env['hr.payslip.line']
        RuleCateg = self.env['hr.salary.rule.category']
        translator = Translator()
        def get_recursive_parent(current_rule_category, rule_categories=None):
            if rule_categories:
                rule_categories = current_rule_category | rule_categories
            else:
                rule_categories = current_rule_category

            if current_rule_category.parent_id:
                return get_recursive_parent(current_rule_category.parent_id, rule_categories)
            else:
                return rule_categories

        res = {}
        result = {}
        if payslip_lines:
            self.env.cr.execute("""
                SELECT pl.id, pl.category_id, pl.slip_id FROM hr_payslip_line as pl
                LEFT JOIN hr_salary_rule_category AS rc on (pl.category_id = rc.id)
                WHERE pl.id in %s
                GROUP BY rc.parent_id, pl.sequence, pl.id, pl.category_id
                ORDER BY pl.sequence, rc.parent_id""",
                (tuple(payslip_lines.ids),))
            for x in self.env.cr.fetchall():
                result.setdefault(x[2], {})
                result[x[2]].setdefault(x[1], [])
                result[x[2]][x[1]].append(x[0])
            for payslip_id, lines_dict in result.items():
                res.setdefault(payslip_id, [])
                for rule_categ_id, line_ids in lines_dict.items():
                    rule_categories = RuleCateg.browse(rule_categ_id)
                    lines = PayslipLine.browse(line_ids)
                    level = 0
                    for parent in get_recursive_parent(rule_categories):
                        res[payslip_id].append({
                            'rule_category': parent.name,
                            'name': parent.name,
                            'code': parent.code,
                            'level': level,
                            'total': sum(lines.mapped('total')),
                        })
                        level += 1
                    for line in lines:
                        res[payslip_id].append({
                            'rule_category': line.name,
                            'name': line.name,
                            'code': line.code,
                            'total': line.total,
                            'level': level
                        })
        # Iterate over all IDs in the 'res' dictionary
        for id_key, items in res.items():
            for item in items:
                item['rule_category'] = self.translate_field(translator, item['rule_category'])
                item['name'] = self.translate_field(translator, item['name'])
                item['code'] = self.translate_field(translator, item['code'])
        return res

    def get_lines_by_contribution_register(self, payslip_lines):
        result = {}
        res = {}
        translator = Translator()
        for line in payslip_lines.filtered('register_id'):
            result.setdefault(line.slip_id.id, {})
            result[line.slip_id.id].setdefault(line.register_id, line)
            result[line.slip_id.id][line.register_id] |= line
        for payslip_id, lines_dict in result.items():
            res.setdefault(payslip_id, [])
            for register, lines in lines_dict.items():
                res[payslip_id].append({
                    'register_name': register.name,
                    'total': sum(lines.mapped('total')),
                })
                for line in lines:
                    res[payslip_id].append({
                        'name': line.name,
                        'code': line.code,
                        'quantity': line.quantity,
                        'amount': line.amount,
                        'total': line.total,
                    })
        for id_key, items in res.items():
            for item in items:
                # Check and translate specific fields if they exist
                if 'register_name' in item:
                    item['register_name'] = self.translate_field(translator, item['register_name'])
                if 'name' in item:
                    item['name'] = self.translate_field(translator, item['name'])
                if 'code' in item:
                    item['code'] = self.translate_field(translator, item['code'])

        return res

    @api.model
    def _get_report_values(self, docids, data=None):

        payslips = self.env['hr.payslip'].browse(docids)
        # Initialize the translator
        translator = Translator()

        # Prepare translations for string fields
        translations = {}
        translations[payslips.id] = {
            "name":translator.translate(payslips.employee_id.name, "Urdu"),
            "designation":translator.translate(payslips.employee_id.job_id.name, "Urdu"),
            "email":payslips.employee_id.work_email,
            "identification_id":payslips.employee_id.identification_id,
            "number":translator.translate(payslips.number, "Urdu"),
            "acc_number":payslips.employee_id.bank_account_id if payslips.employee_id.bank_account_id else "",
            "date_from": self.gregorian_to_islamic_in_urdu(payslips.date_from),
            "date_to":self.gregorian_to_islamic_in_urdu(payslips.date_to)

        }
        print("pay slip Details in urdu translations---------------", translations)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'translations': translations,
            'data': data,
            'get_details_by_rule_category': self.get_details_by_rule_category(payslips.mapped('details_by_salary_rule_category_ids').filtered(lambda r: r.appears_on_payslip)),
            'get_lines_by_contribution_register': self.get_lines_by_contribution_register(payslips.mapped('line_ids').filtered(lambda r: r.appears_on_payslip)),
        }
