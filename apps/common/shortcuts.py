from collections import OrderedDict


def get_template_from_string(template_code):
    from django.template import engines
    template = engines['django'].from_string(template_code)
    return template


def reorder_form_fields(form_fields, field_names_in_order):
    """
    Replacement for Django 1.5 keyOrder field. Also can be used to filter out fields
    """
    return OrderedDict((name, form_fields[name]) for name in field_names_in_order)
