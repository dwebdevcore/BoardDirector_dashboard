# -*- coding: utf-8 -*-
from django.dispatch import Signal

# Similar to django post_save but provides created instance and view request
view_create = Signal(providing_args=['instance', 'request'])
