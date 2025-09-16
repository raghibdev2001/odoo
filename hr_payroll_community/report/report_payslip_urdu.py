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
    _name = 'report.hr_payroll_community.report_payslip_urdu'
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


    def truncate_text(self, text, max_length=50):
        return text + "..."
        # return text[:max_length] + "..." if len(text) > max_length else text

    def payslips_lines(self, payslips):
        lines = []
        translator = Translator()
        for payslip in payslips:
            for line in payslip.line_ids:
                if line.appears_on_payslip:
                    lines.append({
                        "name": self.translate_field(translator, line.name),
                        "code": self.translate_field(translator, line.code),
                        "quantity": line.quantity,
                        "amount": line.amount,
                        "total": line.total,
                    })
        return lines
    @api.model
    def _get_report_values(self, docids, data=None):

        payslips = self.env['hr.payslip'].browse(docids)
        # Initialize the translator
        translator = Translator()

        # Prepare translations for string fields
        translations = {}
        translations[payslips.id] = {
            "name":translator.translate(payslips.employee_id.name, "Urdu"),
            "o_name":self.truncate_text(translator.translate(payslips.name, "Urdu").result),
            "designation":translator.translate(payslips.employee_id.job_id.name, "Urdu") if payslips.employee_id.job_id.name else "",
            "email":payslips.employee_id.work_email,
            "identification_id":payslips.employee_id.identification_id,
            "number":translator.translate(payslips.number, "Urdu") if payslips.number else "",
            "acc_number":payslips.employee_id.bank_account_id if payslips.employee_id.bank_account_id else "",
            "date_from": self.gregorian_to_islamic_in_urdu(payslips.date_from) if payslips.date_from else "",
            "date_to":self.gregorian_to_islamic_in_urdu(payslips.date_to) if payslips.date_to else ""

        }
        # translations[payslips.id] = {
        #     "name":translator.translate(payslips.employee_id.name, "Urdu"),
        #     "o_name":self.truncate_text(translator.translate(payslips.name, "Urdu").result),
        #     "designation":translator.translate(payslips.employee_id.job_id.name, "Urdu"),
        #     "email":payslips.employee_id.work_email,
        #     "identification_id":payslips.employee_id.identification_id,
        #     "number":translator.translate(payslips.number, "Urdu"),
        #     "acc_number":payslips.employee_id.bank_account_id if payslips.employee_id.bank_account_id else "",
        #     "date_from": self.gregorian_to_islamic_in_urdu(payslips.date_from),
        #     "date_to":self.gregorian_to_islamic_in_urdu(payslips.date_to)

        # }

        print("pay slip in urdu translations---------------", translations)
        return {
            'doc_ids': docids,
            'doc_model': 'hr.payslip',
            'docs': payslips,
            'translations': translations,
            'data': data,
            'payslips_lines': {payslips.id:self.payslips_lines(payslips)}
        }