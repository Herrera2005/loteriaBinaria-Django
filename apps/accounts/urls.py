"""Rutas del módulo accounts."""

from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
    path("login/", views.AccountLoginView.as_view(), name="login"),
    path("logout/", views.AccountLogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path(
        "password/change/",
        views.AccountPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "password/change/done/",
        views.AccountPasswordChangeDoneView.as_view(),
        name="password_change_done",
    ),
    path("mode/", views.change_mode, name="choose_mode"),
    path("profile/", views.ProfileDetailView.as_view(), name="profile"),
    path(
        "profile/edit/",
        views.ProfileUpdateView.as_view(),
        name="profile_edit",
    ),
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