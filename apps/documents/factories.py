# -*- coding: utf-8 -*-
import factory
import random

from django.core.files import File
from django.conf import settings
from django.utils import lorem_ipsum
from django.utils.timezone import now

from profiles.models import User
from meetings.models import Meeting
from .models import Document


class DocumentFactory(factory.DjangoModelFactory):

    class Meta:
        model = Document

    name = lorem_ipsum.words(3, True)

    file = File(open(settings.DEFAULT_AVATAR))

    @factory.lazy_attribute
    def created_at(self):
        return now()

    @factory.lazy_attribute
    def user(self):
        return User.objects.all().order_by('?')[0]

    @factory.lazy_attribute
    def type(self):
        return random.choice([i[0] for i in Document.DOCS_TYPES])
