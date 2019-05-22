from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail.message import EmailMessage

from common.models import TemplateModel


def send_voting_email(request, voting, exclude_memberships=None):
    ctx_dict = {
        'voting': voting,
        'site': get_current_site(request),
        'protocol': settings.SSL_ON and 'https' or 'http',
    }

    for voter in voting.voters.all():
        member = voter.membership
        if exclude_memberships and member in exclude_memberships:
            continue

        ctx_dict['recipient'] = member
        ctx_dict['link'] = '{procotol}://{site}{url}'.format(procotol=ctx_dict['protocol'], site=ctx_dict['site'], url=voter.get_voting_url())

        tmpl = TemplateModel.objects.get(name=TemplateModel.VOTING_INVITATION)
        subject = tmpl.generate_title(ctx_dict) or voting.account.name
        message = tmpl.generate(ctx_dict)

        mail = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [member.user.email])
        admin_emails = [m.user.email for m in voting.account.get_admin_memberships() if m.id != member.id]
        if admin_emails:
            mail.extra_headers['Reply-To'] = ', '.join(admin_emails)

        mail.content_subtype = "html"
        mail.send()
