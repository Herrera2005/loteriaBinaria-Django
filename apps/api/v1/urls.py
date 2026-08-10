from django.urls import path

from .views.health import HealthView
from .views.public import (
    PublicEventDetailView,
    PublicEventListView,
    PublicProductDetailView,
    PublicProductListView,
    PublicResultDetailView,
    PublicResultListView,
)
from .views.auth import (
    LoginView,
    LogoutView,
    MeView,
    ModeView,
    ContextView,
)


urlpatterns = [
    path(
        "health/",
        HealthView.as_view(),
        name="v1-health",
    ),

    path(
        "public/products/",
        PublicProductListView.as_view(),
        name="v1-public-product-list",
    ),
    path(
        "public/products/<int:pk>/",
        PublicProductDetailView.as_view(),
        name="v1-public-product-detail",
    ),

    path(
        "public/events/",
        PublicEventListView.as_view(),
        name="v1-public-event-list",
    ),
    path(
        "public/events/<int:pk>/",
        PublicEventDetailView.as_view(),
        name="v1-public-event-detail",
    ),

    path(
        "public/results/",
        PublicResultListView.as_view(),
        name="v1-public-result-list",
    ),
    path(
        "public/results/<int:pk>/",
        PublicResultDetailView.as_view(),
        name="v1-public-result-detail",
    ),
    path(
        "auth/login/",
        LoginView.as_view(),
        name="v1-auth-login",
    ),
    path(
        "auth/me/",
        MeView.as_view(),
        name="v1-auth-me",
    ),
    path(
        "auth/mode/",
        ModeView.as_view(),
        name="v1-auth-mode",
    ),
    path(
        "auth/context/",
        ContextView.as_view(),
        name="v1-auth-context",
    ),
    path(
        "auth/logout/",
        LogoutView.as_view(),
        name="v1-auth-logout",
    ),
]