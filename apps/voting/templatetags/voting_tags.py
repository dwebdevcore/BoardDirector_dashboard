from django import template
from django.utils import timezone

from accounts.account_helper import get_current_account
from voting.models import VotingVoter, Voting

register = template.Library()


@register.simple_tag
def votings_to_attend(request):
    account = get_current_account(request)
    return VotingVoter.objects.filter(
        membership__user=request.user,
        voting__account=account,
        voting__state=Voting.STATE_PUBLISHED,
        voting__start_time__lt=timezone.now(),
        voting__end_time__gt=timezone.now(),
        voting_done=False,
    ).count()
