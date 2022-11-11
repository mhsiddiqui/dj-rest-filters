import django

__version__ = '1.0.1'

if django.VERSION < (3, 2):  # pragma: no cover
    default_app_config = 'djfilters.apps.DjfiltersConfig'
