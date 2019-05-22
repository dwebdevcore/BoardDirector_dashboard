# -*- coding: utf-8 -*-
import datetime
import json

from copy import deepcopy
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from rest_framework.serializers import ListSerializer
from timezone_field import TimeZoneField

from accounts.account_helper import get_current_account, get_current_account_for_url
from accounts.models import Account
from common.models import TemplateModel
from dashboard.models import RecentActivity
from documents.models import Document
from profiles.models import Membership


class LoginRequiredMixin(object):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)


class SelectBoardRequiredMixin(object):
    def dispatch(self, request, *args, **kwargs):
        account = get_current_account(request)
        if account is None or not Account.objects.filter(id=account.id, is_active=True).exists():
            return redirect('accounts:boards')
        return super(SelectBoardRequiredMixin, self).dispatch(request, *args, **kwargs)


class AjaxableResponseMixin(object):
    """
    Mixin to add AJAX support to a form.
    Must be used with an object-based FormView (e.g. CreateView)
    """

    def render_to_json_response(self, context, **response_kwargs):
        data = json.dumps(context)
        response_kwargs['content_type'] = 'application/json'
        return HttpResponse(data, **response_kwargs)

    def form_invalid(self, form):
        response = super(AjaxableResponseMixin, self).form_invalid(form)
        if self.request.is_ajax():
            errors_flat = []
            for error in form.errors.values():
                errors_flat.extend(error)
            return self.render_to_json_response(errors_flat, status=400)
        else:
            return response

    def form_valid(self, form):
        response = super(AjaxableResponseMixin, self).form_valid(form)
        if self.request.is_ajax():
            data = {'pk': self.object.pk, }
            return self.render_to_json_response(data)
        else:
            return response


class ActiveTabMixin(object):
    """
    Mixin to set active tab menu
    """
    active_tab = None

    def get_active_tab(self):
        if self.active_tab is None:
            raise ImproperlyConfigured(
                "ActiveTabMixin requires either a definition of "
                "'active_tab' or an implementation of 'get_active_tab()'")
        return self.active_tab

    def get_context_data(self, **kwargs):
        context = super(ActiveTabMixin, self).get_context_data(**kwargs)
        context['active_tab'] = self.get_active_tab()
        return context


class CurrentAccountMixin(object):
    def get_initial(self):
        initial = super(CurrentAccountMixin, self).get_initial()
        initial['account'] = get_current_account(self.request)
        return initial


class CurrentMembershipMixin(object):
    def get_initial(self):
        initial = super(CurrentMembershipMixin, self).get_initial()
        initial['membership'] = self.request.user.get_membership(get_current_account(self.request))
        return initial


class GetMembershipMixin(object):
    def get_current_membership(self):
        return self.request.user.get_membership(self.get_current_account())

    def get_current_account(self):
        return get_current_account(self.request)


class ApiInitAccountByUrlMixin(object):
    """
    Mixin to force initialization of account by url kwarg.
    """

    def initialize_request(self, request, *args, **kwargs):
        request = super(ApiInitAccountByUrlMixin, self).initialize_request(request, *args, **kwargs)
        get_current_account_for_url(request, self.kwargs.get('url'))
        return request


class GetMembershipWithURLFallbackMixin(object):
    """
    Separate class with fallback as it's unclear what security problems might arise (shouldn't be much, but still, needs verification).
    
    Use in situation where session might not be available. Like in APIs in case of Basic Auth.
    """

    def get_current_membership(self):
        return self.request.user.get_membership(self.get_current_account()) if self.request.user.is_authenticated else None

    def get_current_account(self):
        return get_current_account_for_url(self.request, self.kwargs.get('url'))


# noinspection PyUnresolvedReferences
class AccountSerializerContextMixin(object):
    def get_serializer_context(self):
        s = super(AccountSerializerContextMixin, self)
        context = s.get_serializer_context() if hasattr(s, 'get_serializer_context') else {}
        context['account'] = self.get_current_account()
        context['user'] = user = self.request.user
        context['membership'] = self.request.user.get_membership(self.get_current_account()) if user.is_authenticated else None
        return context


class RecentActivityMixin(object):
    def save_recent_activity(self, action_flag, obj=None):
        obj = obj or self.object
        RecentActivity.objects.create(
            init_user=self.request.user,
            content_type=ContentType.objects.get_for_model(obj),
            object_id=obj.pk,
            action_flag=action_flag,
            account=get_current_account(self.request))


class DocumentFormInvalidMixin(object):
    def form_invalid(self, form):
        self.kwargs['other_docs'] = []
        if form.cleaned_data.get('uploaded', ''):
            docs = form.cleaned_data['uploaded'].split(',')
            documents = Document.objects.filter(id__in=docs)
            for document in documents:
                if document.type == Document.BOARD_BOOK:
                    self.kwargs['doc_board_book'] = document
                elif document.type == Document.AGENDA:
                    self.kwargs['doc_agenda'] = document
                elif document.type == Document.MINUTES:
                    self.kwargs['doc_minutes'] = document
                elif document.type == Document.OTHER:
                    self.kwargs['other_docs'].append(document)
        return self.render_to_response(self.get_context_data(form=form, **self.kwargs))


class MemberNotificationMixin(object):
    def send(self, ctx_dict, attachments=()):
        members = Membership.objects.filter(account=self.object.account) \
            .exclude(Q(user=self.object.user) | Q(user__is_active=False) | Q(user=self.request.user)).select_related('User')
        tmpl = TemplateModel.objects.get(name=TemplateModel.DOC)
        subject = ctx_dict.get('title')
        message = tmpl.generate(ctx_dict)
        for member in members:
            member.user.email_user(subject, message, settings.DEFAULT_FROM_EMAIL, attachments)


class AccountGetObjectMixin(object):
    def get_object(self, queryset=None):
        try:
            account_id = get_current_account(self.request).id
            obj = Account.objects.get(id=account_id)
        except ObjectDoesNotExist:
            raise Http404(_("No account found matching the query"))
        return obj


class GetDataMixin(object):
    def get_export_data(self):
        members = []
        fields = ['first_name', 'last_name', 'phone_number', 'position', 'committees']
        headers = []
        for inst in self.get_queryset():
            member = []
            for field in fields:
                field_obj = inst._meta.get_field(field)
                if field_obj.choices:
                    val = str(getattr(inst, 'get_' + field + '_display')())
                elif field_obj.rel:
                    val = ''
                    for value in getattr(inst, field).all():
                        val += value.__unicode__() + ','
                    val = val[:-1]
                elif isinstance(field_obj, TimeZoneField):
                    val = getattr(inst, field).zone
                else:
                    val = getattr(inst, field) or ''
                    if isinstance(val, datetime.date):
                        val = val.strftime('%Y-%m-%d')
                member.append(val)
                title = field_obj.verbose_name.title()
                if title not in headers:
                    headers.append(title)
            # insert 'e-mail'
            member.insert(2, inst.user.email)

            # insert 'role'
            member.insert(5, inst.get_role_name())

            members.append(member)
        headers.insert(2, 'Email')
        headers.insert(5, 'Role')
        return members, headers


class PerActionSerializerModelViewSetMixin(object):
    def get_serializer_class(self):
        field_name = 'serializer_class_' + self.action
        if hasattr(self, field_name):
            return getattr(self, field_name)

        return super(PerActionSerializerModelViewSetMixin, self).get_serializer_class()


class ReBindListSerializer(ListSerializer):
    def __init__(self, *args, **kwargs):
        self.child = kwargs.pop('child', deepcopy(self.child))
        self.child._delay_bind_account = True
        kwargs['child'] = self.child
        super(ReBindListSerializer, self).__init__(*args, **kwargs)

    def bind(self, field_name, parent):
        super(ReBindListSerializer, self).bind(field_name, parent)
        self.child._delay_bind_account = False
        self.child.bind(field_name, parent)


# noinspection PyUnresolvedReferences
class FilterSerializerByAccountMixin(object):
    """
    A bit complex mixin to work with logic to filter queryset by account field.

    Complexity comes from the fact that context is needed and Serializer can be initialized in two ways:
    - as "main" serializer - so it has context right in the __init__ call
    - as "field" so it won't have context until bind() is called (which isn't called at all in case of main serializer construction

    Also we shouldn't accidentally forget the check. So:
    - you always call it inside __init__ method
    - if 'account' is not in context, then check is postponed to bind method (via overriding instance method with function)
    - in case bind wasn't called and it's just 'account' is missing in context - there is extra check inside `validate()`
      for fields which were postponed but still not filtered.
    """

    def filter_account(self, field, account_field='account'):
        def do_filter():
            account_filter = {account_field: self.context['account']}
            self.fields[field].queryset = self.fields[field].queryset.filter(**account_filter)

        self._filter_account(field, do_filter)

    def filter_account_complex(self, field, fn=None):
        def decorator(fn):
            def do_filter():
                self.fields[field].queryset = fn(self.fields[field].queryset, self.context['account'])

            self._filter_account(field, do_filter)

        if fn:
            return decorator(fn)
        else:
            return decorator

    def filter_account_in_many(self, field, account_field='account'):
        def do_filter():
            account_filter = {account_field: self.context['account']}
            self.fields[field].child_relation.queryset = self.fields[field].child_relation.queryset.filter(**account_filter)

        self._filter_account(field, do_filter)

    def filter_account_in_child(self, field, account_field='account'):
        def do_filter():
            account_filter = {account_field: self.context['account']}
            self.fields[field].child.queryset = self.fields[field].child.queryset.filter(**account_filter)

        self._filter_account(field, do_filter)

    def _filter_account(self, field, do_filter):
        if 'account' in self.context:
            do_filter()
            self.fields[field].is_filtered_by_account = True
        else:
            bind = self.bind

            def filter_in_bind(*args, **kwargs):
                # Black magic: reset cached properties
                self.__dict__.pop('root', None)
                self.__dict__.pop('context', None)

                res = bind(*args, **kwargs)
                if 'account' not in self.context:
                    if getattr(self, '_delay_bind_account', False):
                        return res
                    else:
                        raise KeyError("'account' is not in serializer context")
                do_filter()
                self.fields[field].is_filtered_by_account = True
                return res

            self.bind = filter_in_bind

            if not hasattr(self, 'assert_account_filter'):
                self.assert_account_filter = []
            self.assert_account_filter.append(field)

    def validate(self, attrs):
        if hasattr(self, 'assert_account_filter'):
            for field in self.assert_account_filter:
                assert getattr(self.fields[field], 'is_filtered_by_account', False), \
                    "Looks like 'account' is not present in serializer's context, so field %s was not filtered by account" % field

        return super(FilterSerializerByAccountMixin, self).validate(attrs)
