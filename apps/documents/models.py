    # -*- coding: utf-8 -*-
import os
import tempfile
import subprocess
import shutil

from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.sites.models import Site
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.mail.message import EmailMessage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.template.defaultfilters import date as datefilter
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from jsonfield.fields import JSONField
from mptt.models import MPTTModel, TreeForeignKey
from django.core.files.base import File

from .managers import FolderManager
from common.storage_backends import StableS3BotoStorage
from common.models import TemplateModel
from common.utils import random_hex

if settings.USE_S3:
    file_storage = StableS3BotoStorage(acl='private', file_overwrite=False)
else:
    file_storage = FileSystemStorage()


class Folder(MPTTModel):
    TRASH_NAME = u'Trash'
    MEETINGS_NAME = u'Meeting Documents'
    COMMITTEES_NAME = u'Committee Documents'
    MEMBERSHIPS_NAME = u'Member Documents'
    RESERVED_NAMES = (TRASH_NAME, MEETINGS_NAME, COMMITTEES_NAME, MEMBERSHIPS_NAME)

    name = models.CharField(_('name'), max_length=255)
    parent = TreeForeignKey('self', verbose_name=_('parent'), related_name='children', null=True, blank=True,
                            on_delete=models.CASCADE)
    account = models.ForeignKey('accounts.Account', verbose_name=_('account'), related_name='folders', null=True,
                                on_delete=models.SET_NULL)
    user = models.ForeignKey('profiles.User', verbose_name=_('user'), related_name='folders', null=True, blank=True,
                             on_delete=models.SET_NULL)
    meeting = models.OneToOneField('meetings.Meeting', verbose_name=_('meeting'), blank=True, null=True,
                                   related_name='folder')
    committee = models.OneToOneField('committees.Committee', verbose_name=_('committee'), blank=True, null=True,
                                     related_name='folder')
    membership = models.OneToOneField('profiles.Membership', verbose_name=_('membership'), blank=True, null=True,
                                      related_name='private_folder')
    slug = models.SlugField(_('slug'), unique=True)
    created = models.DateTimeField(_('created'), auto_now_add=True)
    modified = models.DateTimeField(_('modified'), auto_now=True)
    protected = models.BooleanField(_('protected'), default=False,
                                    help_text=_('For special folders like "Trash"'))
    permissions = GenericRelation('permissions.ObjectPermission')

    ordering = models.IntegerField(_('default ordering'), default=2**10, null=True, blank=True)

    objects = FolderManager()

    class MPTTMeta:
        order_insertion_by = ('name',)

    class Meta:
        unique_together = (('parent', 'name'),)
        ordering = ('name',)
        verbose_name = _('folder')
        verbose_name_plural = _('folders')

    def __unicode__(self):
        if self.meeting is not None:
            # Replace meeting id with date in name
            date_str = datefilter(self.meeting.start, 'N j, Y')
            return u'{0} ({1})'.format(self.meeting.name, date_str)
        if self.committee is not None:
            return self.committee.name
        if self.membership is not None:
            return unicode(self.membership)
        return self.name

    def clean(self, *args, **kwargs):
        if self.name and self.name.lower() in [n.lower() for n in Folder.RESERVED_NAMES]:
            raise ValidationError(_('That folder name is system reserved. Please choose another name.'))
        super(Folder, self).clean(*args, **kwargs)

    @classmethod
    def generate_slug(cls):
        exists = True
        while exists:
            slug = random_hex(length=20)
            exists = cls.objects.filter(slug=slug).exists()
        return slug

    @classmethod
    def generate_name_from_meeting(cls, meeting):
        id_str = unicode(meeting.id)
        return u'{0} ({1})'.format(meeting.name[:250 - len(id_str)], id_str)

    @classmethod
    def generate_name_from_committee(cls, committee):
        id_str = unicode(committee.id)
        return u'{0} ({1})'.format(committee.name[:250 - len(id_str)], id_str)

    @classmethod
    def generate_name_from_membership(cls, membership):
        id_str = unicode(membership.id)
        return u'{0} ({1})'.format(unicode(membership)[:250 - len(id_str)], id_str)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = Folder.generate_slug()
        super(Folder, self).save(*args, **kwargs)

    @property
    def is_account_root(self):
        return self.account is not None and self.account.url == self.name and self.level == 0

    @property
    def can_add_folders(self):
        # account root can add (while protected)
        return self.is_account_root or self.committee is not None or self.membership is not None or not self.protected

    @property
    def can_add_files(self):
        # meeting folder can add files (but no folders)
        return self.can_add_folders or self.meeting is not None

    @property
    def sort_date(self):
        # return date used for sorting
        return self.created if self.protected else self.modified

    def get_absolute_url(self):
        return reverse('folders:folder_detail', kwargs={'slug': self.slug, 'url': self.account.url}) if self.account else None

    def get_parents_without_root(self):
        return self.get_ancestors().filter(parent__isnull=False)


class AbstractDocument(models.Model):
    AGENDA, MINUTES, OTHER, BOARD_BOOK = range(1, 5)

    DOCS_TYPES = (
        (AGENDA, _('agenda')),
        (MINUTES, _('minutes')),
        (BOARD_BOOK, _('board_book')),
        (OTHER, _('other')),
    )

    name = models.CharField(_('name'), max_length=250, blank=True)
    file = models.FileField(_('file'), upload_to='uploads/docs/%Y%m%d', storage=file_storage)
    pdf_preview = models.FileField(_('pdf_preview'), upload_to='uploads/docs/%Y%m%d',
                                   storage=file_storage, blank=True, null=True)
    type = models.PositiveIntegerField(verbose_name=_('document type'), choices=DOCS_TYPES, default=OTHER)
    created_at = models.DateTimeField(_('upload date'), default=timezone.now)
    size = models.IntegerField(_('file size'), default=0, null=True, blank=True)
    ordering = models.IntegerField(_('default ordering'), default=2**10, null=True, blank=True)

    def __unicode__(self):
        return self.name if self.name else self.file.name

    class Meta:
        abstract = True

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None, clone=False):
        if not self.pk and not clone:
            name, extension = os.path.splitext(self.file.name)
            self.name = name + extension.lower()
            self.file.name = '{}.{}'.format(random_hex(8), extension[1:])
        super(AbstractDocument, self).save(force_insert, force_update, using, update_fields)

    def extension(self):
        name, extension = os.path.splitext(self.file.name)
        ext = extension[1:].lower()
        if ext in ['xlsx', 'xls']:
            return 'xlsx'
        elif ext == 'pdf':
            return ext
        elif ext in ['docx', 'doc']:
            return 'docx'
        elif ext == 'png':
            return 'png'
        elif ext in ['jpg', 'jpeg']:
            return 'jpeg'
        elif ext in ['tif', 'tiff']:
            return 'tiff'
        elif ext in ['ppt', 'pptx']:
            return 'pptx'
        elif ext == 'mp4':
            return 'mp4'
        elif ext == 'avi':
            return 'avi'
        elif ext == 'zip':
            return 'zip'
        elif ext == 'mp3':
            return 'mp3'
        else:
            return ext

    # Roughly mapping to Font-Awesome file-*-o
    EXTENSION_TO_TYPE_MAPPING = {
        'xlsx': 'excel',
        'docx': 'word',
        'png': 'image',
        'jpeg': 'image',
        'tiff': 'image',
        'pdf': 'pdf',
        'pptx': 'powerpoint',
        'zip': 'archive',
        'mp3': 'audio',
        'ogg': 'audio',
        'odt': 'word',
        'ods': 'excel',
        'odp': 'powerpoint'
    }

    def file_type(self):
        return self.EXTENSION_TO_TYPE_MAPPING.get(self.extension(), 'text')

    @property
    def filename(self):
        if self.type == self.AGENDA:
            return _('Meeting Agenda')
        if self.type == self.MINUTES:
            return _('Meeting Minutes')
        return os.path.basename(self.name or self.file.name)

    @property
    def sort_date(self):
        return self.created_at

    def get_download_url(self):
        return reverse('documents:download', kwargs={'document_id': self.pk})

    def get_api_download_url(self):
        return reverse('api-documents-documents-download', kwargs={'pk': self.pk, 'url': self.account.url})

    def get_api_preview_url(self):
        return reverse('api-documents-documents-download-preview', kwargs={'pk': self.pk, 'url': self.account.url})

    OFFICE_EXTENSIONS = ['docx', 'xlsx', 'pptx', 'doc', 'xls', 'ppt', 'odt', 'ods']
    VIEWABLE_EXTENSIONS = ['jpeg', 'png', 'gif', 'mp4', 'avi']

    def get_viewer_url(self):
        extension = self.extension()
        if extension == 'pdf':
            return static('pdfviewer/web/viewer.html') + '?file=' + self.get_download_url()
        elif extension.lower() in self.OFFICE_EXTENSIONS:
            return static('pdfviewer/web/viewer.html') + '?file=' + reverse('documents:pdf_preview', kwargs={'pk': self.pk})
        elif extension.lower() in self.VIEWABLE_EXTENSIONS:
            return self.get_download_url() + '?view=1'
        else:
            return None

    def get_viewer_or_download_url(self):
        return self.get_viewer_url() or self.get_download_url()

    def generate_preview(self, force=False):

        if self.pdf_preview and not force:
            return self.pdf_preview

        extension = self.extension()
        if extension == 'pdf':
            return self.file
        elif extension.lower() in self.VIEWABLE_EXTENSIONS:
            return self.file
        elif extension.lower() not in self.OFFICE_EXTENSIONS:
            return None

        temp_dir = tempfile.mkdtemp()
        try:
            temp_name = temp_dir + "/temp." + self.extension()
            with open(temp_name, "w+b") as temp, self.file as f:
                # Simple copy because it can be S3
                while True:
                    buf = f.read(1024 * 1024)
                    if not buf:
                        break
                    temp.write(buf)

            process_kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
            }
            # For windows development:
            if os.name != 'nt':
                process_kwargs['close_fds'] = True

            process = subprocess.Popen([settings.LIBRE_OFFICE_BINARY,
                                        '--convert-to', 'pdf',
                                        '--outdir', temp_dir,
                                        temp_name, '--headless'],
                                       **process_kwargs)
            stdout, stderr = process.communicate()
            if process.returncode:
                raise ValueError("Error while calling LibreOffice, code: %d, stdout: %s, stderr: %s" %
                                 (process.returncode, stdout, stderr))

            with open(temp_dir + '/temp.pdf', 'r') as temp:
                name, ext = os.path.splitext(os.path.basename(self.file.path))
                self.pdf_preview.save(name + '.pdf', File(temp))
                self.save()

        finally:
            shutil.rmtree(temp_dir)

        return self.pdf_preview


class Document(AbstractDocument):
    user = models.ForeignKey('profiles.User', verbose_name=_('user'), related_name='documents')
    account = models.ForeignKey('accounts.Account', verbose_name=_('account'), null=True, related_name='documents')
    previous_version = models.PositiveIntegerField(blank=True, null=True)
    folder = TreeForeignKey(Folder, verbose_name=_('folder'), related_name='documents',
                            blank=True, null=True, on_delete=models.SET_NULL)
    permissions = GenericRelation('permissions.ObjectPermission')
    approvals = models.ManyToManyField('profiles.User', through='Approval')

    def get_committee_name(self):
        if self.committee:
            return self.committee.name
        else:
            return _('All Board Members')

    @property
    def revisions(self):
        if hasattr(self, '_revision_cache'):
            return self._revision_cache
        else:
            return list(AuditTrail.objects.filter(latest_version=self.id).order_by('-created_at'))

    @staticmethod
    def prefetch_revisions(documents):
        all_revisions = AuditTrail.objects.filter(latest_version__in=[d.id for d in documents]).order_by('-created_at')
        revision_by_document_id = {}
        for revision in all_revisions:
            revision_by_document_id.setdefault(revision.latest_version, []).append(revision)

        for document in documents:
            document._revision_cache = revision_by_document_id.get(document.id, [])

    def send_notification_email(self, members):

        ctx_dict = {
            'document': self,
            'site': Site.objects.get_current(),
            'protocol': settings.SSL_ON and 'https' or 'http',
            'previous_versions': self.revisions
        }

        for member in members:
            tmpl = TemplateModel.objects.get(name=TemplateModel.DOCUMENT_UPDATED)
            subject = tmpl.title or self.account.name  # fixme: which one?
            message = tmpl.generate(ctx_dict)

            mail = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [member.user.email])
            mail.content_subtype = "html"

            mail.send()

    def approved_user_ids(self):
        """ """
        return self.approval_set.values_list('user_id', flat=True).distinct()


class AuditTrail(AbstractDocument):
    UPDATED, DELETED = range(2)

    CHANGES_TYPES = (
        (UPDATED, _('update')),
        (DELETED, _('deleted'))
    )

    user = models.ForeignKey('profiles.User', verbose_name=_('user'), related_name='audits')
    change_type = models.PositiveIntegerField(verbose_name=_('type of changes'), choices=CHANGES_TYPES, default=UPDATED)
    latest_version = models.PositiveIntegerField(blank=True, null=True)
    revision = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        unique_together = (('latest_version', 'revision'),)

    def get_download_url(self):
        return reverse('documents:download-revision', kwargs={
            'document_id': self.latest_version, 'revision': self.revision})

    def save(self, *args, **kwargs):
        # set revision
        ids = list(Document.objects.filter(Q(previous_version=self.latest_version) | Q(
            previous_version=Document.objects.filter(id=self.latest_version).values_list(
                'previous_version', flat=True))).order_by('id').values_list('id', flat=True))
        if ids:
            latest_id = ids.pop()
            for doc_id in ids:  # rarely used, in best case never
                at = AuditTrail.objects.filter(latest_version=doc_id)
                at.update(latest_version=latest_id)
            revision = AuditTrail.objects.filter(latest_version=latest_id).count() + 1
        else:
            revision = 1
        self.revision = revision
        super(AuditTrail, self).save(*args, clone=True, **kwargs)


class Annotation(models.Model):
    # Note: choices are for reference only currently as mobile app can add new types on the go. So it isn't choices in model.
    TYPE_PEN, TYPE_HIGHLIGHTER, TYPE_STICKY_NOTE, TYPE_STICKY_TAB = range(1, 5)
    TYPE_CHOICES = [
        (TYPE_PEN, _('Pen')),
        (TYPE_HIGHLIGHTER, _('Highlighter')),
        (TYPE_STICKY_NOTE, _('Sticky Note')),
        (TYPE_STICKY_TAB, _('Sticky Tab')),
    ]

    account = models.ForeignKey('accounts.Account', on_delete=models.CASCADE, related_name='annotations')
    author_user = models.ForeignKey('profiles.User', on_delete=models.CASCADE, related_name='annotations')
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True, related_name='annotations')
    audit_trail = models.ForeignKey(AuditTrail, on_delete=models.CASCADE, null=True,
                                    blank=True, related_name='annotations')
    document_page = models.PositiveIntegerField()
    type = models.PositiveSmallIntegerField()
    created = models.DateTimeField(auto_now_add=True)
    shared = models.BooleanField(default=False)  # Annotation is visible (and commentable to other users)

    geometry_tools_version = models.PositiveSmallIntegerField()
    cargo_json = JSONField()
    local_id = models.CharField(max_length=255, null=True, blank=True)


class AnnotationComment(models.Model):
    annotation = models.ForeignKey(Annotation, on_delete=models.CASCADE, related_name='comments')
    author_user = models.ForeignKey('profiles.User', on_delete=models.CASCADE, related_name='annotation_comments')
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)


class Approval(models.Model):
    document = models.ForeignKey(Document)
    user = models.ForeignKey('profiles.User')

# import after models
from . import signals  # noqa
