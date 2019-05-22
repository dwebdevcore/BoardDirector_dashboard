# -*- coding: utf-8 -*-
from accounts.account_helper import get_current_account


class FormValidMixin(object):
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.account = get_current_account(self.request)
        self.object.created_member = self.request.user.get_membership(self.object.account)
        self.object.save()
        self.get_success_message()
        return super(FormValidMixin, self).form_valid(form)
