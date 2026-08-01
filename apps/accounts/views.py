"""Vistas de autenticación, registro y selección de modo."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .access import ACTIVE_MODE_SESSION_KEY, assigned_mode_codes
from .forms import ModeSelectionForm, RegistrationForm, TallerAuthenticationForm
from .models import User
from .roles import DASHBOARD_URL_NAMES, ROLE_PRESENTATION


def _client_ip(request) -> str | None:
    return request.META.get("REMOTE_ADDR") or None


class AccountLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = TallerAuthenticationForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        modes = assigned_mode_codes(user)

        if len(modes) == 1:
            active_mode = modes[0]
            self.request.session[ACTIVE_MODE_SESSION_KEY] = active_mode
            destination = reverse(DASHBOARD_URL_NAMES[active_mode])
        elif len(modes) > 1:
            self.request.session.pop(ACTIVE_MODE_SESSION_KEY, None)
            destination = reverse("accounts:choose_mode")
        else:
            self.request.session.pop(ACTIVE_MODE_SESSION_KEY, None)
            messages.warning(
                self.request,
                "La cuenta no tiene roles asignados; contacta al administrador.",
            )
            destination = reverse("core:home")

        messages.success(self.request, "Sesión iniciada correctamente.")
        return HttpResponseRedirect(destination)


class AccountLogoutView(LogoutView):
    next_page = "core:home"
    http_method_names = ["post", "options"]


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("core:home")

    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            form.save(ip_address=_client_ip(request))
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(
                request,
                "Cuenta creada. Ya puedes iniciar sesión.",
            )
            return redirect("accounts:login")

    return render(request, "accounts/register.html", {"form": form})


@require_http_methods(["GET", "POST"])
def choose_mode(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if not request.user.is_active or request.user.status != User.Status.ACTIVE:
        raise PermissionDenied("La cuenta no está activa para cambiar de modo.")

    modes = assigned_mode_codes(request.user)
    current = request.session.get(ACTIVE_MODE_SESSION_KEY)
    form = ModeSelectionForm(
        request.POST or None,
        assigned_modes=modes,
    )

    if request.method == "POST" and form.is_valid():
        selected = form.cleaned_data["mode"]
        request.session[ACTIVE_MODE_SESSION_KEY] = selected
        messages.success(
            request,
            f"Modo {ROLE_PRESENTATION[selected]['label']} activado.",
        )
        return redirect(DASHBOARD_URL_NAMES[selected])

    assigned_modes = [
        {
            "code": code,
            **ROLE_PRESENTATION[code],
            "is_active": code == current,
        }
        for code in modes
    ]
    return render(
        request,
        "accounts/choose_mode.html",
        {"form": form, "assigned_modes": assigned_modes},
    )
