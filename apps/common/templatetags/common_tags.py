# -*- coding: utf-8 -*-
import os
from json import dumps

from django import template
from django.conf import settings
from django.template.base import TemplateSyntaxError, kwarg_re, Node
from django.utils.encoding import smart_text
from django.utils.safestring import mark_safe
from django.utils.six import text_type
from django.utils.translation import ugettext as _

from accounts.account_helper import get_current_account
from common.models import UpdateNotification
from documents.models import Document

register = template.Library()


@register.simple_tag(takes_context=True)
def acc_document(context, pk, *args, **kwargs):
    return Document.objects.filter(account=get_current_account(context['request']), group__pk=pk).order_by('-created_at')


@register.tag()
def acc_url(parser, token):
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (path to a view)" % bits[0])
    try:
        viewname = parser.compile_filter(bits[1])
    except TemplateSyntaxError as exc:
        exc.args = (exc.args[0] + ". "
                                  "The syntax of 'url' changed in Django 1.5, see the docs."),
        raise
    args = []
    kwargs = {}
    asvar = None
    bits = bits[2:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to url tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))

    return URLNode(viewname, args, kwargs, asvar)


@register.filter
def bool_to_checked(value):
    return value and "checked" or ""


@register.filter
def check_choice_value(choice_field, value):
    return choice_field.valid_value(value)


@register.filter
def folder_display_name(folder, membership):
    try:
        if folder.is_account_root:
            return _(u'Documents')
        elif folder.membership_id == membership.id:
            return _(u'My Documents')
        else:
            return unicode(folder)
    except:
        return ''


@register.simple_tag(takes_context=True)
def update_notifications_for_user(context):
    request = context['request']
    user = request.user

    if user.is_anonymous:
        return []
    else:
        return list(UpdateNotification.objects.filter(is_active=True, publish_date__gte=user.date_notifications_read).order_by('publish_date'))


class URLNode(Node):
    def __init__(self, view_name, args, kwargs, asvar):
        self.view_name = view_name
        self.args = args
        self.kwargs = kwargs
        self.asvar = asvar

    def render(self, context):
        from django.core.urlresolvers import reverse, NoReverseMatch
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_text(k, 'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        kwargs['url'] = get_current_account(context['request']).url

        view_name = self.view_name.resolve(context)

        if not view_name:
            raise NoReverseMatch("'url' requires a non-empty first argument. "
                                 "The syntax changed in Django 1.5, see the docs.")

        # Try to look up the URL twice: once given the view name, and again
        # relative to what we guess is the "main" app. If they both fail,
        # re-raise the NoReverseMatch unless we're using the
        # {% url ... as var %} construct in which case return nothing.
        url = ''
        current_app = context['request'].resolver_match.app_name
        try:
            url = reverse(view_name, args=args, kwargs=kwargs, current_app=current_app)
        except NoReverseMatch as e:
            if settings.SETTINGS_MODULE:
                project_name = settings.SETTINGS_MODULE.split('.')[0]
                try:
                    url = reverse(project_name + '.' + view_name,
                                  args=args, kwargs=kwargs,
                                  current_app=current_app)
                except NoReverseMatch:
                    if self.asvar is None:
                        # Re-raise the original exception, not the one with
                        # the path relative to the project. This makes a
                        # better error message.
                        raise e
            else:
                if self.asvar is None:
                    raise e

        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            return url


@register.filter
def attrs(value, arg):
    """
    DANGER! This tag alters original widget object. It's handy but can't be used with
    dynamic class switching.
    """
    attrs = value.field.widget.attrs

    kvs = arg.split(',')

    for string in kvs:
        kv = string.split(':')
        attrs[kv[0].strip()] = kv[1].strip()

    rendered = str(value)

    return rendered


@register.simple_tag()
def field_errors(field):
    if field and field.errors:
        return mark_safe("""
            <span class="k-widget k-tooltip k-tooltip-validation k-invalid-msg" data-for="%s" role="alert">
            <span class="k-icon k-warning"></span>
                %s
            </span>
            """ % (field.auto_id, field.errors[0]))
    else:
        return ""


@register.simple_tag()
def field_errors_with_field_name(field):
    """
    Formats errors for field, including it's name. Useful for displaying hidden field errors.
    """
    if field.errors:
        return mark_safe("""
            <span class="k-widget k-tooltip k-tooltip-validation k-invalid-msg" data-for="%s" role="alert">
                    <span class="k-icon k-warning"></span>
                    <span class="field-name">%s:</span> %s
            </span>
            """ % (field.auto_id, text_type(field.label), field.errors[0]))
    else:
        return ""


@register.simple_tag
def get_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag
def get_social_mapping(key):
    return settings.SOCIAL_MAPPING.get(key)


@register.simple_tag
def get_social_profile_icon(sauth):
    if sauth.provider:
        return sauth.provider.split('-', 1)[0]
    return None


@register.simple_tag
def get_social_profile_name(sauth):

    if sauth.provider == 'google-oauth2':
        return sauth.uid

    elif sauth.provider == 'twitter' and sauth.extra_data:
        return sauth.extra_data.get('access_token', {}).get('screen_name')

    elif sauth.provider == 'linkedin-oauth2' and sauth.extra_data:
        fn = sauth.extra_data.get('first_name', u'')
        ln = sauth.extra_data.get('last_name', u'')
        name = u"%s %s" % (fn, ln)
        return name.strip()

    return None


@register.simple_tag
def get_social_profile_url(sauth):

    if sauth.provider == 'google-oauth2':
        return "mailto:%s" % (sauth.uid)

    elif sauth.provider == 'twitter' and sauth.extra_data:
        sn = sauth.extra_data.get('access_token', {}).get('screen_name')
        return "https://twitter.com/%s" % (sn)

    return None


@register.filter
def min_for_prod(resource):
    if settings.DEBUG:
        return resource
    else:
        return resource.replace('.js', '.min.js').replace('.css', '.min.css')


@register.filter
def json(data):
    return mark_safe(dumps(data))


@register.filter
def file_basename(file):
    """
    :func: remove file extension
    :param file: for example file="Financial Report.pdf"
    :return: "Financial Report"
    """
    name, extension = os.path.splitext(file)
    return name


@register.filter
def custom_social_name(social_name):
    if 'Google' in social_name:
        return 'Google'
    return social_name
