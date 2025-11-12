"""Routes HTTP du chatbot."""
from __future__ import annotations

from django.urls import path

from .views import widget

app_name = "chatbot"

urlpatterns = [
    path("widget/", widget, name="widget"),
]
