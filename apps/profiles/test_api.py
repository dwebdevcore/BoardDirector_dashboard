from django.core import mail

from common.utils import AccJsonRequestsTestCase


class CheckEmailTestCase(AccJsonRequestsTestCase):
    def setUp(self):
        self.create_init_data()

    def test_responses(self):
        self.assertEqual({'result': 'not-exists'}, self.acc_get('api-profiles-check-email-list').json())
        self.assertEqual({'result': 'not-exists'}, self.acc_get('api-profiles-check-email-list', data={'email': 'wrong-email'}).json())
        self.assertEqual({'result': 'exists'}, self.acc_get('api-profiles-check-email-list', data={'email': self.user.email}).json())
        self.assertEqual({'result': 'exists'}, self.acc_get('api-profiles-check-email-list', data={'email': self.admin.email}).json())

        self.user.is_active = False
        self.user.save()
        self.assertEqual({'result': 'inactive'}, self.acc_get('api-profiles-check-email-list', data={'email': self.user.email}).json())

    def test_reset_password(self):
        self.acc_post_json('api-profiles-reset-password-list', {'email': self.user.email}, account_url=None, assert_status_code=200)
        self.assertEqual(1, len(mail.outbox))  # Just check it triggers
