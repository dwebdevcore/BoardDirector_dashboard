# -*- coding: utf-8 -*-
import factory

from django.contrib.auth.hashers import make_password
from django.utils import lorem_ipsum

from profiles.models import User, Membership


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    @factory.lazy_attribute_sequence
    def email(self, n):
        return u'{0}_{1}@example{2}.com'.format(self.accounts[0].id, lorem_ipsum.words(1, False), n)

    password = make_password('member')

    @factory.post_generation
    def accounts(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        # A list of groups were passed in, use them
        for account in extracted:
            if not kwargs.get('role'):
                kwargs['role'] = Membership.ROLES.member
            Membership.objects.create(user=self, account=account,
                                      first_name=lorem_ipsum.words(1, False).capitalize(),
                                      last_name=lorem_ipsum.words(1, False).capitalize(),
                                      **kwargs)

    is_active = True


class AdminFactory(UserFactory):

    @factory.lazy_attribute_sequence
    def email(self, n):
        return u'acc_{0}_admin@example{1}.com'.format(self.accounts[0].id, n)

    password = make_password('admin')

    @factory.post_generation
    def accounts(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        # A list of groups were passed in, use them
        for account in extracted:
            Membership.objects.create(user=self, account=account, is_admin=True,
                                      first_name=lorem_ipsum.words(1, False).capitalize(),
                                      last_name=lorem_ipsum.words(1, False).capitalize())


class ChairpersonFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    @factory.lazy_attribute_sequence
    def email(self, n):
        return u'{0}_{1}@example{2}.com'.format(self.accounts[0].id, lorem_ipsum.words(1, False), n)

    password = make_password('member')

    @factory.post_generation
    def accounts(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        # A list of groups were passed in, use them
        for account in extracted:
            Membership.objects.create(user=self, account=account, role=Membership.ROLES.chair,
                                      first_name=lorem_ipsum.words(1, False).capitalize(),
                                      last_name=lorem_ipsum.words(1, False).capitalize())

    is_active = True
