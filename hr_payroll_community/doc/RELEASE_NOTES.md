## Module <hr_payroll_community>
#### 28.11.2023
#### Version 17.0.1.0.0
#### ADD

- Initial commit for Odoo17 Payroll

#### 06.06.2024
#### Version 17.0.1.0.1
#### UPDT

- Updated payroll report

https://fonts.google.com/selection?preview.text=tareekh%20se

sudo mkdir -p /usr/share/fonts/truetype/urdu
cd /usr/share/fonts/truetype/urdu
sudo wget https://github.com/google/fonts/raw/main/ofl/notonastaliqurdu/NotoNastaliqUrdu-Regular.ttf
sudo fc-cache -fv


fc-list | grep "Noto Nastaliq Urdu"



/home/raghib/Documents/odoo-custom-addons/hr_payroll_community/report/report_payslip_urdu_templates.xml

                    <style>
                            @font-face {
                                font-family: 'Noto Nastaliq Urdu';
                                src: url('/usr/share/fonts/truetype/urdu/static/NotoNastaliqUrdu-Regular.ttf') format('truetype');
                            }
                            body {
                                font-family: 'Noto Nastaliq Urdu', 'DejaVu Sans', sans-serif;
                                direction: rtl;
                                text-align: right;
                                font-size: 14px;
                                line-height: 1.8;
                            }
                            .urdu2-font {
                                font-family: 'Noto Nastaliq Urdu', 'DejaVu Sans', sans-serif;
                                direction: rtl;
                                text-align: right;
                            }
                            td, th {
                                font-family: 'Noto Nastaliq Urdu', 'DejaVu Sans', sans-serif !important;
                            }
                        </style>