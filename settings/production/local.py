import os

ALLOWED_HOSTS = ['127.0.0.1', '52.8.2.195']
DOMAIN = os.environ.get('DOMAIN')
if DOMAIN is not None:
    ALLOWED_HOSTS.insert(0, DOMAIN)


