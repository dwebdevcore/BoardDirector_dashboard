from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from common.models import AuthToken
from common.utils import AccJsonRequestsTestCase


class TokenAuthTest(AccJsonRequestsTestCase):
    def setUp(self):
        self.create_init_data()

    def test_login_logout(self):
        token = self.acc_post_json('token-auth-list', {
            'username': self.admin.email,
            'password': 'admin',
        }, assert_status_code=201, account_url=self.NO_URL).json()

        self.assertTrue(token['token'])
        self.assertEquals(self.admin.email, token['user']['email'])
        self.assertEquals(self.account.url, token['user']['accounts'][0]['url'])
        self.assertEquals(1, len(token['user']['accounts']))
        self.assertEquals(1, len(token['user']['memberships']))
        self.assertEquals(self.membership_admin.first_name, token['user']['memberships'][0]['first_name'])

        token = AuthToken.objects.get(token=token['token'])

        # Check request
        meetings_url = '/{url}/api/v1/meetings/meetings/'.format(url=self.account.url)
        result = self.client.get(meetings_url, follow=True)
        self.assertEquals(401, result.status_code)

        result = self.client.get(meetings_url, HTTP_AUTHORIZATION='token WRONG-TOKEN', follow=True)
        self.assertEquals(401, result.status_code)

        result = self.client.get(meetings_url, HTTP_AUTHORIZATION='token ' + token.token, follow=True)
        self.assertEquals(200, result.status_code)

        # Check token is too old
        token.created -= timedelta(days=settings.REST_TOKEN_MAX_AGE_DAYS + 1)
        token.save()

        result = self.client.get(meetings_url, HTTP_AUTHORIZATION='token ' + token.token, follow=True)
        self.assertEquals(401, result.status_code)

        # Check logout
        token.created = timezone.now()
        token.save()

        result = self.client.get(meetings_url, HTTP_AUTHORIZATION='token ' + token.token, follow=True)
        self.assertEquals(200, result.status_code)

        result = self.client.post('/api/v1/token-auth/logout/', HTTP_AUTHORIZATION='token ' + token.token)
        self.assertEquals(200, result.status_code)

        result = self.client.get(meetings_url, HTTP_AUTHORIZATION='token ' + token.token, follow=True)
        self.assertEquals(401, result.status_code)

    def test_me(self):
        self.login_admin()
        me = self.acc_get('me-list', account_url=self.NO_URL).json()
        self.assertEquals(self.admin.email, me['email'])
        self.assertEquals(self.account.url, me['accounts'][0]['url'])
