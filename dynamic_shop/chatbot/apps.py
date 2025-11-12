from __future__ import annotations

from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dynamic_shop.chatbot"
    verbose_name = "Chatbot"
