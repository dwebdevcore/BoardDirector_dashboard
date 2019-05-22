from django.contrib.staticfiles.apps import StaticFilesConfig
from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class NoNodeStaticFilesConfig(StaticFilesConfig):
    ignore_patterns = ['CVS', '.*', '*~', 'node_modules']


class MercifulManifestStaticFilesStorage(ManifestStaticFilesStorage):
    def hashed_name(self, name, content=None, filename=None):
        try:
            return super(MercifulManifestStaticFilesStorage, self).hashed_name(name, content, filename)
        except ValueError as e:
            # Don't die in case of absent file (there is a couple of old minified css, so that it's easier to keep exceptions here)
            for legacy in ['{{{spriteUrl}}}', 'css/textures', 'chosen-sprite']:
                if legacy in name:
                    return 'not-found-' + name
            raise e
