# -*- coding: utf-8 -*-
from django import forms

from .models import RsvpResponse


class RsvpResponseForm(forms.ModelForm):
    response_text = forms.CharField()  # RSVP UI has close relation with display_text, so this is processed separately

    class Meta:
        model = RsvpResponse
        fields = ('accept_type', 'note')
        widgets = {}
