# -*- coding: utf-8 -*-
from storages.backends.s3boto import S3BotoStorage


class StableS3BotoStorage(S3BotoStorage):

    def _open(self, name, mode='rb'):
        name = self._normalize_name(self._clean_name(name))
        f = self.file_class(name, mode, self)
        if not f.key:
            if 'default_avatar.png' in name:
                raise IOError('File does not exist: %s' % name)
            else:
                return self._open('images/default_avatar.png', mode)
        return f
