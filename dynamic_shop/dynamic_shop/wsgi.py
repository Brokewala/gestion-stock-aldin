"""WSGI config pour l'exécution via Gunicorn."""
from __future__ import annotations

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dynamic_shop.dynamic_shop.settings")

application = get_wsgi_application()
