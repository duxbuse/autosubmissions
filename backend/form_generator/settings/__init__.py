import os

env = os.environ.get('DJANGO_ENV', 'local')

if env == 'compose':
    from .settings_compose import *
else:
    from .settings_local import *