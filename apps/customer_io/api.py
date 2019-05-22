# -*- coding: utf-8 -*-
import logging
from customerio import CustomerIO
from django.conf import settings


logger = logging.getLogger(__name__)


class CIOApi(object):
    """Wrapper for CustomerIO python library."""
    def __init__(self):
        super(CIOApi, self).__init__()
        self.cio = CustomerIO(settings.CUSTOMERIO_SITE_ID, settings.CUSTOMERIO_API_KEY)

    def api_call(func):
        """Wrapper for API cals."""
        def wrapped_func(*args, **kwargs):
            args_str = u', '.join(unicode(a) for a in args[1:])
            args_str += u', '.join(unicode(v) for v in kwargs.values())
            logger.debug(u'CustomerIO api call: %s %s' % (func.__name__, args_str))
            if not settings.CUSTOMERIO_ENABLED:
                return None
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(e)
        return wrapped_func

    @api_call
    def create_or_update(self, membership):
        self.cio.identify(
            id=membership.id,
            email=membership.user.email,
            created_at=membership.user.date_joined,
            last_login=membership.last_login,
            short_name=membership.get_short_name(),
            full_name=membership.get_full_name(),
            role=membership.get_role_display(),
            account_name=membership.account.name,
            account_plan=membership.account.plan.get_name_display(),
            account_is_trial=membership.account.is_trial(),
            account_is_active=membership.account.is_active,
            account_date_cancel=membership.account.date_cancel,
            account_date_created=membership.account.date_created,
        )

    @api_call
    def track_event(self, membership, name, **kwargs):
        self.cio.track(customer_id=membership.id, name=name, **kwargs)

    @api_call
    def delete(self, membership):
        self.cio.delete(customer_id=membership.id)
