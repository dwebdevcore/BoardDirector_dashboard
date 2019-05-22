# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from sorl.thumbnail import delete

from accounts.account_helper import get_current_account
from common.middleware import TimezoneMiddleware
from profiles.models import User, Membership, TemporaryUserPassword


class MembershipQuerysetMixin(object):
    """Use on view/add/edit/delete membership views"""

    def get_queryset(self):
        account = get_current_account(self.request)
        cur_membership = self.request.user.get_membership(account)
        if cur_membership.is_admin:
            return Membership.objects.filter(account=account)
        return Membership.objects.filter(account=account, is_active=True)


class AvatarSaveMixin(object):
    def avatar_save(self, form):
        x1 = form.cleaned_data.get('x1')
        y1 = form.cleaned_data.get('y1')
        x2 = form.cleaned_data.get('x2')
        y2 = form.cleaned_data.get('y2')
        if all([i is not None for i in (x1, x2, y1, y2)]) and self.object.avatar:
            self.object = self.get_queryset().get(pk=self.object.pk)

            # remove previous crop
            if self.object.crops:
                self.object.crops.delete('rect')

            scale = float(self.object.avatar.width) / 240

            # sanity check for cropping area (and reset)
            if x1 == x2 or y1 == y2 or x1 > x2 or y1 > y2 or x2 < 0 or y2 < 0:
                x1, x2 = 1, self.object.avatar.width - 1
                y1, y2 = 1, self.object.avatar.height - 1
                scale = 1.0

            self.object.crops.create('rect', (int(x1 * scale), int(y1 * scale),
                                              int((x2 - x1) * scale), int((y2 - y1) * scale)))
            delete(self.object.crops.rect, delete_file=False)

        self.object.save()


class MemberCreateMixin(AvatarSaveMixin):
    def form_save(self, form):
        self.object = form.save(commit=False)
        self.tmppasswd = password = User.objects.make_random_password()
        user = User.objects.create_user(email=form.cleaned_data['email'], password=password)
        self.object.user = user
        self.object.account = get_current_account(self.request)
        self.object.save()
        self.avatar_save(form)
        self.get_success_message()
        TemporaryUserPassword.objects.create(user=user, password=password)

    def get_context_data(self, *args, **kwargs):
        context = super(MemberCreateMixin, self).get_context_data(*args, **kwargs)
        context['default_avatar_url'] = settings.DEFAULT_AVATAR_URL
        return context


class MemberEditMixin(AvatarSaveMixin):
    def get_form_kwargs(self):
        kwargs = super(MemberEditMixin, self).get_form_kwargs()
        kwargs['instance'] = get_object_or_404(self.get_queryset().select_related('user'), pk=self.kwargs['pk'])
        kwargs['initial'].update({'email': kwargs['instance'].user.email})
        return kwargs

    def form_valid(self, form):

        self.object = membership = form.save(commit=False)
        membership.save()

        membership.user.refresh_from_db()
        membership.user.email = form.cleaned_data['email']

        # password field not empty
        if form.cleaned_data.get('password1'):
            membership.user.set_password(form.cleaned_data['password1'])

        membership.user.save()

        form.save_m2m()  # committees
        self.avatar_save(form)

        if not membership.is_active:
            membership.deactivate()  # Can be called multiple times

        if self.request.user == membership.user:
            TimezoneMiddleware.reset_timezone(self.request, membership)

        messages.success(self.request, _('Profile was changed successfully.'))
        return super(MemberEditMixin, self).form_valid(form)
