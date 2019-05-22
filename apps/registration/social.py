from django.shortcuts import redirect, get_object_or_404
from django.urls.base import reverse
from django.utils.http import urlencode
from social_core.pipeline.partial import partial

from profiles.models import User


@partial
def redirect_new_user_to_registration(backend, strategy, details, user, *args, **kwargs):
    if user:
        return {}

    if 'registered_user_id' in strategy.request.session:
        new_user = get_object_or_404(User, pk=strategy.request.session.pop('registered_user_id'))

        cleanup_social_auth_from_session(strategy)

        return {
            'user': new_user
        }

    view = 'registration_register_frame' if strategy.session_get('is_frame') == '1' else 'registration_register'

    strategy.session_set('social_details', details)
    strategy.session_set('social_last_backend', backend.name)  # Sticky now, used only in registration as WP can't pass it via GET

    return strategy.redirect(reverse(view))



def cleanup_social_auth_from_session(strategy):
    strategy.session_pop('partial_pipeline_token')  # Weird, need to reset pipeline otherwise it's sticky.
    strategy.session_pop('social_details')
    strategy.session_pop('social_last_backend')

def cleanup_social_auth_from_session_by_request(request):
    request.session.pop('partial_pipeline_token', None)  # Weird, need to reset pipeline otherwise it's sticky.
    request.session.pop('social_details', None)
    request.session.pop('social_last_backend', None)


