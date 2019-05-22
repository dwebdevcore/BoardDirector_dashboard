from billing.models import BillingSettings
from committees.models import Committee
from profiles.models import Membership
from django.utils.translation import ugettext_lazy as _


def init_account(account, user):
    BillingSettings.objects.create(name=account.name, mail=user.email, account=account)
    membership = Membership.objects.create(user=user, account=account, is_admin=True)
    board_of_directors = Committee.objects.create(name=_('Full Board'), account=account)
    board_of_directors.chairman.add(membership)
    membership.committees.add(board_of_directors)
