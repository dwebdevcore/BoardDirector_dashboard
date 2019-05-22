from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import TemplateView
from permissions import PERMISSIONS

from common.mixins import GetMembershipMixin, SelectBoardRequiredMixin, ActiveTabMixin, GetMembershipWithURLFallbackMixin
from permissions.mixins import PermissionMixin
from voting.models import Voting


class VotingMainView(ActiveTabMixin, SelectBoardRequiredMixin, PermissionMixin, TemplateView, GetMembershipMixin):
    permission = (Voting, PERMISSIONS.view)
    template_name = 'voting/voting.html'
    active_tab = 'voting'

    def get_context_data(self, **kwargs):
        data = super(VotingMainView, self).get_context_data(**kwargs)
        data['is_admin'] = self.get_current_membership().is_admin
        return data


# Note: No LoginRequired out of the box as this view can be accessed anonymously with VoterKey
class VotingVoteView(TemplateView, GetMembershipWithURLFallbackMixin):
    template_name = 'voting/voting_vote.html'

    def get_context_data(self, **kwargs):
        data = super(VotingVoteView, self).get_context_data(**kwargs)
        if 'voter_key' in kwargs:
            # This way doesn't require current user to be in place
            voter_key = kwargs['voter_key']
        elif self.request.user.is_anonymous():
            raise PermissionDenied(_('Must be authorized to access this url'))
        else:
            voting = get_object_or_404(Voting.objects.filter(account__url=kwargs['url']), pk=kwargs['pk'])
            voter = voting.voters.get(membership=self.get_current_membership())
            voter_key = voter.voter_key

        data['voter_key'] = voter_key

        if self.request.user.is_anonymous:
            self.get_current_account()  # Side-effect this will set current account by url for this request, makes acc_url and other things work fine.

        return data
