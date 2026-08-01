"""Rutas del módulo accounts."""

from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("login/", views.AccountLoginView.as_view(), name="login"),
    path("logout/", views.AccountLogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("mode/", views.choose_mode, name="choose_mode"),
    path("users/", views.UserListView.as_view(), name="user_list"),
    path("users/create/", views.UserCreateView.as_view(), name="user_create"),
    path(
        "users/<int:pk>/",
        views.UserDetailView.as_view(),
        name="user_detail",
    ),
    path(
        "users/<int:pk>/edit/",
        views.UserUpdateView.as_view(),
        name="user_update",
    ),
    path(
        "users/<int:pk>/delete/",
        views.UserDeleteDeactivateView.as_view(),
        name="user_delete",
    ),
]