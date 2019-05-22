from django.conf.urls import url, include
from rest_framework import routers

from voting import api_views

from voting.views import VotingMainView, VotingVoteView

router = routers.DefaultRouter()
router.register(r'voting/votings', api_views.VotingViewSet, base_name='api-voting-votings')
router.register(r'voting/votings/(?P<voting>\d+)/questions', api_views.QuestionViewSet, base_name='api-voting-questions')
router.register(r'voting/votings/(?P<voting>\d+)/voters', api_views.VoterViewSet, base_name='api-voting-voters')
router.register(r'voting/available-votings', api_views.AvailableVotingsViewSet, base_name='api-voting-available-votings')
router.register(r'voting/vote-voting', api_views.VoteVotingViewSet, base_name='api-voting-vote-voting')

app_name = 'voting'

urlpatterns = [
    url(r'^$', VotingMainView.as_view(), name='voting-main'),
    url(r'^vote/(?P<pk>\d+)/$', VotingVoteView.as_view(), name='voting-vote-by-pk'),
    url(r'^vote-by-key/(?P<voter_key>[\w\d]+)/$', VotingVoteView.as_view(), name='voting-vote-by-key'),  # For external links without auth
]
