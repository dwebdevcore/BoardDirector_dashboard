# -*- coding: utf-8 -*-
from django import forms
from django.db import models


class BigIntegerSizeFormField(forms.IntegerField):

    def to_python(self, value):
        if not value:
            value = 0
        value = super(BigIntegerSizeFormField, self).to_python(value)
        value *= 1024 ** 3
        return value

    def prepare_value(self, value):
        if not value:
            value = 0
        value = int(super(BigIntegerSizeFormField, self).prepare_value(value))
        value /= 1024 ** 3
        return value


class BigIntegerSizeField(models.BigIntegerField):
    def formfield(self, **kwargs):
        defaults = {
            'min_value': -BigIntegerSizeField.MAX_BIGINT - 1,
            'max_value': BigIntegerSizeField.MAX_BIGINT,
            'form_class': BigIntegerSizeFormField,
        }
        defaults.update(kwargs)
        return super(BigIntegerSizeField, self).formfield(**defaults)
