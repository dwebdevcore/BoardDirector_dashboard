# -*- coding: utf-8 -*-
from django.utils import lorem_ipsum
from django.core.urlresolvers import reverse

from accounts.account_helper import set_current_account, get_current_account
from accounts.factories import AccountFactory
from common.utils import BaseTestCase as TestCase
from news.factories import NewsFactory
from news.models import News
from profiles.factories import UserFactory, AdminFactory


class NewsTest(TestCase):

    def setUp(self):
        self.create_init_data()
        self.news = NewsFactory(account=self.account)
        self.client.login(username=self.admin.email, password='admin')
        self.session = self.client.session
        set_current_account(self, self.account)
        self.session.save()

    def test_detail_view(self):
        url = reverse('news:detail', kwargs={'pk': self.news.pk, 'url': get_current_account(self).url})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.news.title)
        self.assertContains(response, self.news.text[:100])

    def test_list_view(self):
        news2 = NewsFactory(account=self.account)
        url = reverse('news:list', kwargs={'url': get_current_account(self).url})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.news.title.title())
        self.assertContains(response, news2.title.title())

    def test_create(self):
        url = reverse('news:create', kwargs={'url': get_current_account(self).url})
        data = {
            'title': lorem_ipsum.words(2, False),
            'text': lorem_ipsum.words(5, True),
            'is_publish': True
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'News was added successfully.')

    def test_update(self):
        url = reverse('news:edit', kwargs={'pk': self.news.pk, 'url': get_current_account(self).url})
        data = {
            'title': lorem_ipsum.words(2, False),
            'text': lorem_ipsum.words(5, True)
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'News was updated successfully.')
        self.assertEqual(News.objects.get(pk=self.news.pk).title, data['title'])

    def test_update_wrong(self):
        user = UserFactory(accounts=[self.account])
        self.login_member(user.email)
        url = reverse('news:edit', kwargs={'pk': self.news.pk, 'url': get_current_account(self).url})
        data = {
            'title': lorem_ipsum.words(2, False),
            'text': lorem_ipsum.words(5, True),
            'is_publish': True
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 403)

    def test_delete_news_forbidden(self):
        self.login_admin()
        new_acc = AccountFactory()
        AdminFactory(accounts=[new_acc])
        news2 = NewsFactory(account=new_acc)
        url = reverse('news:delete', kwargs={'pk': news2.pk, 'url': get_current_account(self).url})
        response = self.ajax(url)
        self.assertEqual(response.status_code, 404)

    def test_delete_news(self):
        self.login_admin()
        url = reverse('news:delete', kwargs={'pk': self.news.pk, 'url': get_current_account(self).url})
        response = self.ajax(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(News.objects.filter(id=self.news.pk).exists())
