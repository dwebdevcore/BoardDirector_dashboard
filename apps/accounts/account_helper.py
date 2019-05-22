from django.core.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from django.utils.translation import ugettext_lazy as _


def set_current_account(request, account):
    request.session['current_account_id'] = account.id
    request.current_account = account


def get_current_account(request):
    if not hasattr(request, 'current_account'):
        if 'current_account_id' in request.session:
            # To remove circular dependency
            from accounts.models import Account

            request.current_account = Account.objects.get(pk=request.session['current_account_id'])
        else:
            request.current_account = None

    return request.current_account


def get_current_account_for_url(request, url):
    session_account = get_current_account(request)
    if session_account:
        if url and session_account.url != url:
            raise PermissionDenied(_("Account in URL doesn't match account in session."))
        return session_account

    if url:
        from accounts.models import Account
        url_account = get_object_or_404(Account, url=url)
        set_current_account_temp(request, url_account)
        return url_account
    else:
        raise ValueError("Account not found nor in SESSION nor in URL")


def set_current_account_temp(request, account):
    """Just sets cached value but no session storage"""
    request.current_account = account


def clear_current_account(request):
    if hasattr(request, 'current_account'):
        del request.current_account

    del request.session['current_account_id']
