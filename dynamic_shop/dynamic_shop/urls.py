"""Déclaration des URLs principales du projet DYNAMIC."""
from __future__ import annotations

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="API DYNAMIC",
        default_version="v1",
        description="Documentation interactive de l'API DYNAMIC.",
        contact=openapi.Contact(email="support@dynamic.bo"),
        license=openapi.License(name="Propriétaire - DYNAMIC"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("", include("dynamic_shop.core.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("dynamic_shop.api.urls")),
    path("inventory/", include("dynamic_shop.inventory.urls")),
    path("sales/", include("dynamic_shop.sales.urls")),
    path("chatbot/", include("dynamic_shop.chatbot.urls")),
    re_path(r"^api/docs/?$", schema_view.with_ui("swagger", cache_timeout=0), name="api-docs"),
    re_path(r"^api/redoc/?$", schema_view.with_ui("redoc", cache_timeout=0), name="api-redoc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
