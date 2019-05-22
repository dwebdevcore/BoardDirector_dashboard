# -*- coding: utf-8 -*-
from django import template
from django.utils.translation import ugettext_lazy as _


register = template.Library()


@register.filter
def arraylookup(a, idx):
    """
    Gets a value from an iterable.
    :param a: array / list / other monad.
    :param idx: aray index (zero based).
    :return: element, or None if not found.
    """
    if not a:
        return None
    elif len(a) <= idx:
        return None
    else:
        return a[idx]


@register.filter
def selectplan(plan):
    """
    Add the word "select" (i18n translated) before the label of the radio button.
    Hence <plan name> becomes "select <plan name>".
    :param plan: widget
    :return: modified version of the input, with the word "select" pasted before its label.
    """
    if hasattr(plan, "choice_label"):
        plan.choice_label = _("select {}".format(plan.choice_label))
    return plan
