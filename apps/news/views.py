# -*- coding: utf-8 -*-
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from accounts.account_helper import get_current_account
from common.mixins import AjaxableResponseMixin, SelectBoardRequiredMixin, ActiveTabMixin
from news.forms import NewsForm
from news.mixins import FormValidMixin
from news.models import News
from permissions import PERMISSIONS
from permissions.mixins import PermissionMixin
from permissions.shortcuts import has_role_permission


class NewsQuerysetMixin(object):
    def get_queryset(self):
        account = get_current_account(self.request)
        membership = self.request.user.get_membership(account)
        queryset = News.objects.filter(account=account)
        if has_role_permission(membership, News, PERMISSIONS.edit):
            return queryset
        return queryset.filter(Q(is_publish=True) | Q(created_member=membership))


class NewsListView(SelectBoardRequiredMixin, NewsQuerysetMixin, PermissionMixin, ActiveTabMixin, ListView):
    permission = (News, PERMISSIONS.view)
    template_name = 'news/news_list.html'
    paginate_by = 6
    active_tab = 'news'


class NewsDetailView(SelectBoardRequiredMixin, NewsQuerysetMixin, PermissionMixin, ActiveTabMixin, DetailView):
    permission = (News, PERMISSIONS.view)
    template_name = 'news/news_detail.html'
    active_tab = 'news'


class NewsCreateView(SelectBoardRequiredMixin, PermissionMixin, FormValidMixin, ActiveTabMixin, CreateView):
    permission = (News, PERMISSIONS.add)
    form_class = NewsForm
    template_name = "news/news_update.html"
    active_tab = 'news'

    def get_success_message(self):
        messages.success(self.request, _('News was added successfully.'))

    def get_success_url(self):
        return reverse('news:list', kwargs={'url': get_current_account(self.request).url})


class NewsUpdateView(SelectBoardRequiredMixin, NewsQuerysetMixin, PermissionMixin, FormValidMixin, ActiveTabMixin, UpdateView):
    permission = (News, PERMISSIONS.edit)
    form_class = NewsForm
    template_name = "news/news_update.html"
    active_tab = 'news'

    def get_success_message(self):
        messages.success(self.request, _('News was updated successfully.'))

    def get_success_url(self):
        return reverse('news:detail', kwargs={'pk': self.kwargs['pk'], 'url': get_current_account(self.request).url})


class NewsDeleteView(AjaxableResponseMixin, SelectBoardRequiredMixin, NewsQuerysetMixin, PermissionMixin, DeleteView):
    permission = (News, PERMISSIONS.delete)

    def delete(self, request, *args, **kwargs):
        super(NewsDeleteView, self).delete(request, *args, **kwargs)
        messages.success(request, _('News was deleted.'))
        return self.render_to_json_response({'url': self.get_success_url()})

    def get_success_url(self):
        return reverse('news:list', kwargs={'url': get_current_account(self.request).url})
