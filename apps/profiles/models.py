# -*- coding: utf-8 -*-
import urlparse

from croppy.fields import CropField
from django.conf import settings
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.contrib.auth.signals import user_logged_in
from django.contrib.sites.models import Site
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from django.dispatch import receiver
from django.shortcuts import get_object_or_404
from django.template import Context
from django.utils import timezone
from django.utils.translation import ugettext as _

# from croppy.fields import CropField
from sorl.thumbnail import get_thumbnail
from timezone_field.fields import TimeZoneField

from accounts.models import Account
from committees.models import Committee
from common.choices import Choices
from common.models import TemplateModel
from common.shortcuts import get_template_from_string
from common.storage_backends import StableS3BotoStorage
from common.utils import avatar_upload_to, crops_upload_to


if settings.USE_S3:
    avatar_storage = StableS3BotoStorage(file_overwrite=False)
else:
    avatar_storage = FileSystemStorage(location=settings.AVATAR_ROOT, base_url=settings.AVATAR_URL)


class UserManager(BaseUserManager):

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = UserManager.normalize_email(email)

        extra_fields.pop('username', None)  # Passed by social auth, not needed here

        user = self.model(email=email, is_staff=False, is_active=True, is_superuser=False, **extra_fields)

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        u = self.create_user(email, password, **extra_fields)
        u.is_staff = True
        u.is_active = True
        u.is_superuser = True
        u.save(using=self._db)
        return u

    def get_by_natural_key(self, username):
        return self.get(**{self.model.USERNAME_FIELD + '__iexact': username})


class User(AbstractBaseUser):
    email = models.EmailField(_('email address'), unique=True)

    is_staff = models.BooleanField(_('staff status'), default=False,
                                   help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True,
                                    help_text=_('Designates whether this user should be treated as '
                                                'active. Unselect this instead of deleting accounts.'))
    is_superuser = models.BooleanField(_('superuser status'), default=False,
                                       help_text=_('Designates that this user has all permissions without '
                                                   'explicitly assigning them.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    accounts = models.ManyToManyField(Account, through='Membership', verbose_name=_('accounts'),
                                      related_name='users')

    date_notifications_read = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    objects = UserManager()

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def _get_name(self):
        memberships = self.membership_set.all()
        if memberships:
            return {"first": memberships[0].first_name,
                    "last": memberships[0].last_name}
        else:
            return None

    def get_full_name(self):
        n = self._get_name()
        if n:
            full_name = u"{0} {1}".format(n.get("first"), n.get("last")).strip()
        else:
            full_name = None
        return full_name or self.email

    def get_short_name(self):
        n = self._get_name()
        if n:
            first_name = n.get("first", "").strip()
        else:
            first_name = None
        return first_name or self.email.split('@')[0]

    def get_membership(self, account):
        if account is None:
            raise ValueError("account is None")

        membership_name = '_membership_{}'.format(account.id)
        if not hasattr(self, membership_name):
            membership = get_object_or_404(Membership, user=self, account=account)
            setattr(self, membership_name, membership)
        return getattr(self, membership_name)

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def get_absolute_url(self):
        return reverse('profiles:detail', kwargs={'pk': self.pk})

    def __unicode__(self):
        return self.email

    def send_invitation_email(self, account, password=None, message=None, from_member=None):
        site = Site.objects.get_current()
        ctx_dict = {'account': account, 'user': self}
        ctx_dict['inviter'] = str(from_member or 'Someone')
        protocol = settings.SSL_ON and 'https' or 'http'
        ctx_dict['protocol'] = protocol
        if password:
            ctx_dict['password'] = password
            ctx_dict['profile_detail_url'] = \
                urlparse.urljoin('{}://{}'.format(protocol, site),
                                 reverse('profiles:detail',
                                         kwargs={'pk': self.get_membership(account).pk}))
        ctx_dict['board_detail_url'] = urlparse.urljoin('{}://{}'.format(protocol, site),
                                                        reverse('board_detail', kwargs={'url': account.url}))
        ctx_dict['login_link'] = urlparse.urljoin('{}://{}'.format(protocol, site), reverse('auth_login'))
        if message:
            # Fixme: should it be preprocessed?
            ctx_dict['message'] = message

        tmpl = TemplateModel.objects.get(name=TemplateModel.INVITE)
        subject = tmpl.title
        message = tmpl.generate(ctx_dict)
        self.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

    def admin_notification(self, account, msg_type='cancel_account'):
        site = Site.objects.get_current()
        ctx_dict = {'account': account, 'site': site, 'user': self, 'protocol': settings.SSL_ON and 'https' or 'http'}
        tmpl, message = '', ''
        if msg_type == 'cancel_account':
            ctx_dict['url'] = reverse('accounts:boards')
            tmpl = TemplateModel.objects.get(name=TemplateModel.CANCEL)
            message = tmpl.generate(ctx_dict)
        elif msg_type == 'trial_is_over':
            ctx_dict['url'] = reverse('billing:update_settings')
            if account.stripe_customer_id:
                tmpl = TemplateModel.objects.get(name=TemplateModel.TRIAL)
            else:
                tmpl = TemplateModel.objects.get(name=TemplateModel.TRIAL_IS_OVER_CANCEL)
            message = tmpl.generate(ctx_dict)
        elif msg_type == 'paid_is_over':
            tmpl = TemplateModel.objects.get(name=TemplateModel.PAID)
            message = tmpl.generate(ctx_dict)
        elif msg_type == 'trial_reminder':
            ctx_dict['date_cancel'] = (account.date_created +
                                       timezone.timedelta(days=settings.TRIAL_PERIOD)).strftime('%b %d, %Y')
            tmpl = TemplateModel.objects.get(name=TemplateModel.TRIAL_REMINDER)
            message = tmpl.generate(ctx_dict)

        subject = get_template_from_string(tmpl.title)
        subject = subject.render(ctx_dict)
        self.email_user(subject, message, settings.DEFAULT_FROM_EMAIL)

    def email_user(self, subject, message, from_email=None, attachments=()):
        """
        Sends an email to this User.
        """
        msg = EmailMessage(subject, message, from_email, [self.email])
        for name, attach, content_type in attachments:
            msg.attach(name, attach, content_type)
        msg.content_subtype = 'html'
        msg.send()


class Membership(models.Model):

    ROLES = Choices(
        # 'member' roles
        (2, 'member', _('Board Member')),
        (21, 'director', _('Executive Director')),
        (20, 'ceo', _('CEO')),
        (1, 'chair', _('Board Chair')),

        # 'guest' roles
        (6, 'staff', _('Staff')),
        (4, 'guest', _('Guest')),
        (5, 'vendor', _('Vendor')),
        (7, 'consultant', _('Consultant')),
        (3, 'assistant', _('Executive Assistant')),
    )
    STATUS = Choices(
        (True, 'active', _('Active')),
        (False, 'inactive', _('Inactive')),
    )
    INV_NOT_SENT, INV_SENT, INV_INVITED = range(3)
    INV_CHOICES = (
        (INV_NOT_SENT, 'NOT_SENT'),
        (INV_SENT, 'SENT'),
        (INV_INVITED, 'INVITED'))

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assistant = models.ForeignKey('self', related_name='bosses',
                                  blank=True, null=True, on_delete=models.SET_NULL)

    # Member Details
    account = models.ForeignKey(Account, related_name='memberships')
    committees = models.ManyToManyField(Committee, verbose_name=_('committees'),
                                        related_name='memberships', blank=True)

    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    phone_number = models.CharField(_('phone number'), max_length=255, blank=True)
    secondary_phone = models.CharField(_('secondary phone'), max_length=255, blank=True)

    role = models.PositiveSmallIntegerField(_('role'), choices=ROLES, default=ROLES.member)
    # Admin can name them anything they wish?
    # Internally, they will be categorized as Guests/Members but the Display title will be different.
    custom_role_name = models.CharField(_('custom role name'), max_length=50, blank=True)

    is_active = models.BooleanField(_('active'), choices=STATUS, default=True)
    is_admin = models.BooleanField(_('admin'), default=False)

    date_joined_board = models.DateField(_('date joined board'), default=timezone.now)
    term_start = models.DateField(_('starts'), blank=True, null=True)
    term_expires = models.DateField(_('expires'), blank=True, null=True)
    timezone = TimeZoneField()

    # Work details
    employer = models.CharField(_('employer'), max_length=255, blank=True)
    job_title = models.CharField(_('job title'), max_length=255, blank=True)
    work_email = models.CharField(_('work email'), max_length=255, blank=True)
    work_number = models.CharField(_('work number'), max_length=255, blank=True)
    work_address = models.CharField(_('address'), max_length=255, blank=True)
    work_secondary_address = models.CharField(_('secondary address'), max_length=255, blank=True)
    work_city = models.CharField(_('city'), max_length=50, blank=True)
    work_state = models.CharField(_('state'), max_length=50, blank=True)
    work_zip = models.CharField(_('zip'), max_length=50, blank=True)
    work_country = models.CharField(_('country'), max_length=50, blank=True)

    # Bio graphy
    intro = models.CharField(_('intro'), max_length=250, blank=True)
    bio = models.TextField(_('bio'), blank=True)

    # Personal details
    title = models.CharField(_('title'), max_length=225, blank=True)
    description = models.TextField(_('description'), blank=True)
    address = models.CharField(_('address'), max_length=255, blank=True)
    secondary_address = models.CharField(_('secondary address'), max_length=255, blank=True)
    city = models.CharField(_('city'), max_length=50, blank=True)
    state = models.CharField(_('state'), max_length=50, blank=True)
    zip = models.CharField(_('zip'), max_length=50, blank=True)
    country = models.CharField(_('country'), max_length=50, blank=True)
    birth_date = models.CharField(_('birth date'), max_length=100, blank=True)

    # Social Details
    affiliation = models.CharField(_('affiliations'), max_length=255, blank=True)
    social_media_link = models.CharField(_('social media links'), max_length=255, blank=True)

    # Avatar
    avatar = models.ImageField(storage=avatar_storage, upload_to=avatar_upload_to, blank=True)
    crops = CropField('avatar', upload_to=crops_upload_to)
    position = models.CharField(_('position'), max_length=250, blank=True)

    # Notes
    notes = models.TextField(_('notes'), blank=True)

    # Other
    last_login = models.DateTimeField(_('last login'), null=True, editable=False)
    last_modified = models.DateTimeField(_('last modified date'), editable=False, auto_now=True)
    invitation_status = models.PositiveSmallIntegerField(_('invitation status'),
                                                         choices=INV_CHOICES, default=INV_NOT_SENT)

    @property
    def is_invited(self):
        return self.invitation_status == self.INV_INVITED

    @property
    def invitation_sent(self):
        return self.invitation_status != self.INV_NOT_SENT

    def deactivate(self):
        self.is_active = False
        for boss in self.bosses.all():
            boss.assistant = None
            boss.save()

        if self.assistant:
            assistant = self.assistant
            if assistant.bosses.count() == 1:
                assistant.is_active = False
                assistant.save()

            # Drop association
            self.assistant = None

        self.save()

    class Meta:
        unique_together = ('user', 'account')
        ordering = ('first_name', 'last_name')

    def __unicode__(self):
        return self.get_full_name()

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        if self.first_name and self.last_name:
            full_name = u'{} {}'.format(self.first_name, self.last_name)
            return full_name.strip()
        return self.user.email.split('@')[0]

    def get_short_name(self):
        return self.first_name

    def get_role_name(self):
        if self.custom_role_name is None or self.custom_role_name == '':
            return self.get_role_display()
        else:
            return self.custom_role_name

    def avatar_url(self, geometry=''):
        if self.avatar:
            try:
                if geometry:
                    if self.crops:
                        return get_thumbnail(self.crops.rect, geometry, crop='center', quality=100).url
                    if 'x' in geometry:
                        return get_thumbnail(self.avatar, geometry, crop='center', quality=100).url
                    else:
                        return get_thumbnail(self.avatar, geometry, quality=100).url
                else:
                    return self.avatar.url
            except:
                pass
        return settings.DEFAULT_AVATAR_URL

    def list_avatar_url(self, geometry='180x120'):
        if self.avatar:
            return get_thumbnail(self.avatar, geometry, crop='center', quality=100).url
        return settings.DEFAULT_LIST_AVATAR_URL

    @property
    def is_staff(self):
        return self.role == Membership.ROLES.staff

    @property
    def is_guest(self):
        return self.role in (Membership.ROLES.assistant, Membership.ROLES.guest, Membership.ROLES.vendor,
                             Membership.ROLES.staff, Membership.ROLES.consultant)

    @property
    def can_have_assistant(self):
        return self.role in (Membership.ROLES.chair, Membership.ROLES.member)

    def is_committee_chairman(self, committee=None):
        """Checks if member is committee chair or assistant of chair."""
        if self.role == Membership.ROLES.assistant:
            ids = self.get_bosses().values_list('id', flat=True)
        else:
            ids = [self.id]
        if committee is not None:
            return committee.chairman.filter(id__in=ids).exists()
        else:
            return Committee.objects.filter(chairman__id__in=ids).exists()

    def get_bosses(self):
        return self.bosses.filter(is_active=True)

    def get_absolute_url(self):
        return reverse('profiles:detail', kwargs={'pk': self.pk})

    @property
    def get_affiliation(self):
        return ', '.join(self.affiliation.split(','))

    @property
    def get_phone(self):
        return ', '.join(self.phone_number.split(','))

    @property
    def get_phones(self):
        phones = filter(lambda x: x is not None and len(x) > 6,
                        [self.phone_number, self.secondary_phone])
        return phones


class TemporaryUserPassword(models.Model):
    user = models.OneToOneField(User, related_name='tmppswd')
    password = models.CharField(_('password'), max_length=128)


#  signal receivers connects here
@receiver(user_logged_in)
def remove_tmppswd(sender, request, user, **kwargs):
    TemporaryUserPassword.objects.filter(user=user).delete()
