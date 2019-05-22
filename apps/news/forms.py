# -*- coding: utf-8 -*-
from django import forms
from django.utils.translation import ugettext_lazy as _

from news.models import News


class NewsForm(forms.ModelForm):
    class Meta:
        model = News
        fields = ('title', 'text', 'file', 'is_publish')
        widgets = {
            'text': forms.Textarea(attrs={'class': 'kendo_editor'}),
            'title': forms.TextInput(attrs={'class': 'txt title title-news', 'placeholder': _('Untitled Article')}),
            'file': forms.FileInput(attrs={'class': 'avatar-input'})
        }
