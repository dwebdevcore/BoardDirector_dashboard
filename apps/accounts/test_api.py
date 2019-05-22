from accounts.models import Account
from billing.models import Plan
from common.api.exception_handler import WRONG_REQUEST
from common.utils import AccJsonRequestsTestCase
from profiles.models import Membership


class ApiTestCase(AccJsonRequestsTestCase):
    def setUp(self):
        self.create_init_data()
        self.init_second_account()

    def test_account(self):
        self.acc_get('api-accounts-accounts-list', account_url=self.NO_URL, assert_status_code=401)  # Require auth

        self.login_admin()
        accounts = self.acc_get('api-accounts-accounts-list', account_url=self.NO_URL).json()
        self.assertEqual(4, len(accounts))  # 4 ?! some test data is created.

        account = self.acc_post_json('api-accounts-accounts-list', account_url=self.NO_URL, json_data={
            'url': 'test-account',
            'name': 'Test Account',
        }).json()
        self.assertEqual('test-account', account['url'])
        self.assertEqual('Test Account', account['name'])
        self.assertEqual(Plan.DEFAULT_PLAN, account['plan'])

        account = Account.objects.get(pk=account['id'])
        self.assertTrue(account.billing_settings)
        self.assertEqual(1, len(account.users.all()))
        self.assertEqual(self.admin, account.users.all()[0])
        self.assertTrue(self.admin.get_membership(account).is_admin)

        # Verify details url
        account_json = self.acc_get('api-accounts-accounts-detail', account_url=self.NO_URL, pk=account.id).json()
        self.assertEqual('test-account', account_json['url'])

        # Regular user can't update nor delete
        Membership.objects.create(account=account, user=self.user)
        self.login_member()

        # Regular member can read details
        account_json = self.acc_get('api-accounts-accounts-detail', account_url=self.NO_URL, pk=account.id).json()
        self.assertEqual('test-account', account_json['url'])

        # But not update
        self.acc_put_json('api-accounts-accounts-detail', account_url=self.NO_URL, pk=account.id, json_data={
            'url': 'I`m a hacker',
            'name': 'Wrong update',
        }, assert_status_code=403)

        self.acc_delete('api-accounts-accounts-detail', account_url=self.NO_URL, pk=account.id,
                        assert_status_code=403)

        self.login_admin()

        # Test update errors: unique and slug
        update = self.acc_put_json('api-accounts-accounts-detail', account_url=self.NO_URL, pk=account.id, json_data={
            'url': self.account.url,
            'name': 'Wrong update',
        }, assert_status_code=400).json()
        self.assertEqual({'url': ['account with this url already exists.'], 'detail': WRONG_REQUEST}, update)

        update = self.acc_put_json('api-accounts-accounts-detail', account_url=self.NO_URL, pk=account.id, json_data={
            'url': 'INValid Slug',
            'name': 'Wrong update',
        }, assert_status_code=400).json()
        self.assertEqual({'url': ['Enter a valid "slug" consisting of letters, numbers, underscores or hyphens.'], 'detail': WRONG_REQUEST}, update)

        # Test successful update
        update = self.acc_put_json('api-accounts-accounts-detail', account_url=self.NO_URL, pk=account.id, json_data={
            'url': 'Updated-URL',
            'name': 'Good update',
        }).json()
        self.assertEqual('Updated-URL', update['url'])

        # Finish it
        self.assertTrue(Account.objects.filter(pk=account.id).exists())
        self.acc_delete('api-accounts-accounts-detail', account_url=self.NO_URL, pk=account.id)
        self.assertFalse(Account.objects.filter(pk=account.id).exists())

    def test_check_account(self):
        self.assertEqual('not-exists', self.acc_get('api-accounts-accounts-check-exists', account_url=self.NO_URL).json()['result'])
        self.assertEqual('not-exists', self.acc_get('api-accounts-accounts-check-exists', account_url=self.NO_URL, data={'url': 'adda12d'}).json()['result'])
        self.assertEqual('exists', self.acc_get('api-accounts-accounts-check-exists', account_url=self.NO_URL, data={'url': self.account.url}).json()['result'])
        self.account.is_active = False
        self.account.save()
        self.assertEqual('inactive', self.acc_get('api-accounts-accounts-check-exists', account_url=self.NO_URL, data={'url': self.account.url}).json()['result'])
