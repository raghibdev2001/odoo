odoo.define('your_module_name', ['web.public.widget'], function (require) {
    "use strict";

    const publicWidget = require('web.public.widget');

    publicWidget.registry.SlidePrintButton = publicWidget.Widget.extend({
        selector: '.o_wslides_fs_container, .o_wslides_lesson_content',
        start() {
            console.log("Asdfasfa")
            this._addPrintButton();
            return this._super.apply(this, arguments);
        },
        _addPrintButton() {
            const iframe = this.el.querySelector('iframe');
            const src = iframe ? iframe.src : '';
            const isPrintable = /\.(pdf|docx?|jpg|jpeg|png|gif|bmp)$/i.test(src);
            if (isPrintable && !this.el.querySelector('#print-slide-btn')) {
                const btn = document.createElement('button');
                btn.id = 'print-slide-btn';
                btn.innerText = 'Print';
                btn.className = 'btn btn-primary o_print_slide_btn';
                btn.style.position = 'absolute';
                btn.style.top = '20px';
                btn.style.right = '20px';
                btn.style.zIndex = 10000;
                btn.onclick = () => {
                    const newWindow = window.open(src, '_blank');
                    if (newWindow) {
                        newWindow.focus();
                        newWindow.print();
                    } else {
                        alert("Popup blocked. Please allow popups for this site.");
                    }
                };
                this.el.appendChild(btn);
            }
        }
    });
});