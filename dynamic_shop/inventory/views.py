"""Vues spécifiques à l'inventaire."""
from __future__ import annotations

from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from .models import Batch


@login_required
def expiry_report(request):
    """Affiche les lots qui expirent dans moins de 30 jours."""

    limit_date = timezone.now().date() + timedelta(days=30)
    batches = Batch.objects.filter(expiry_date__isnull=False, expiry_date__lte=limit_date)
    return render(request, "inventory/expiry_report.html", {"batches": batches, "limit_date": limit_date})
