# -*- coding: utf-8 -*-
from django import forms
from django.utils.safestring import mark_safe
from .models import Feedback, TemplateModel


class ContactForm(forms.ModelForm):
    class Meta:
        model = Feedback
        exclude = []


class RichTextWidget(forms.Textarea):
    class Media:
        css = {
            'all': ('css/kendo.common.min.css', 'css/kendo.default.min.css')
        }
        js = ('js/jquery-1.8.3.min.js', 'js/kendo.web.min.js', 'js/preview.js')

    def render(self, name, value, attrs=None, renderer=None):
        return mark_safe(super(RichTextWidget, self).render(name, value, attrs, renderer))


class TemplateForm(forms.ModelForm):

    preview_html = forms.CharField(required=False,
                                   widget=RichTextWidget(attrs={'class': 'kendo_editor',
                                                                'style': 'height: 600px; width: 75%;'}))

    def __init__(self, *args, **kwargs):
        super(TemplateForm, self).__init__(*args, **kwargs)
        self.fields['preview_html'].initial = kwargs['instance'].html

    class Meta:
        model = TemplateModel
        exclude = []
        widgets = {
          'html': forms.Textarea(attrs={'style': 'height: 400px; width: 75%; font-family: monospace;'})
        }
