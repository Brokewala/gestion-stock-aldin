"""Vues HTTP pour le chatbot."""
from __future__ import annotations

from django.shortcuts import render


def widget(request):
    """Affiche le widget autonome embarqué via iframe."""

    return render(request, "chatbot/widget.html")
