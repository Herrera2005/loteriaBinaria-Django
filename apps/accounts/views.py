"""Vistas de autenticación, registro, modo y CRUD administrativo de usuarios."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import (
    LoginView,
    PasswordChangeDoneView,
    PasswordChangeView,
)
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied, ValidationError
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View


from .access import (
    ACTIVE_MODE_SESSION_KEY,
    assigned_mode_codes,
    get_valid_active_mode,
)
from .forms import (
    ModeSelectionForm,
    ProfileUpdateForm,
    RegistrationForm,
    TallerAuthenticationForm,
    TallerPasswordChangeForm,
    UserBusinessChangeForm,
    UserBusinessCreationForm,
)
from .mixins import AdministratorModeRequiredMixin
from .models import User
from .roles import (
    DASHBOARD_URL_NAMES,
    ROLE_PRESENTATION,
    VENDOR,
)
from .services import (
    delete_or_deactivate_user,
    user_has_related_history,
)


LOGIN_NEXT_SESSION_KEY = "accounts_safe_login_next"


def _safe_next_url(request) -> str | None:
    """Acepta redirecciones únicamente hacia este mismo host."""
    candidate = (
        request.POST.get("next")
        or request.GET.get("next")
        or ""
    ).strip()
    if not candidate:
        return None
    if url_has_allowed_host_and_scheme(
        candidate,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return candidate
    return None


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
        safe_next = _safe_next_url(self.request)

        if len(modes) == 1:
            active_mode = modes[0]
            self.request.session[ACTIVE_MODE_SESSION_KEY] = active_mode
            destination = safe_next or reverse(
                DASHBOARD_URL_NAMES[active_mode]
            )
        elif len(modes) > 1:
            self.request.session.pop(ACTIVE_MODE_SESSION_KEY, None)
            if safe_next:
                self.request.session[LOGIN_NEXT_SESSION_KEY] = safe_next
            else:
                self.request.session.pop(LOGIN_NEXT_SESSION_KEY, None)
            destination = reverse("accounts:choose_mode")
        else:
            self.request.session.pop(ACTIVE_MODE_SESSION_KEY, None)
            self.request.session.pop(LOGIN_NEXT_SESSION_KEY, None)
            messages.warning(
                self.request,
                "La cuenta no tiene roles asignados; contacta al administrador.",
            )
            destination = reverse("core:home")

        messages.success(self.request, "Sesión iniciada correctamente.")
        return HttpResponseRedirect(destination)


class AccountLogoutView(View):
    http_method_names = ["post", "options"]

    def post(self, request, *args, **kwargs):
        logout(request)
        messages.success(request, "Sesión cerrada correctamente.")
        return redirect("core:home")


class AccountPasswordChangeView(
    LoginRequiredMixin,
    PasswordChangeView,
):
    form_class = TallerPasswordChangeForm
    template_name = "accounts/password_change_form.html"
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Tu contraseña se actualizó correctamente.",
        )
        return response


class AccountPasswordChangeDoneView(
    LoginRequiredMixin,
    PasswordChangeDoneView,
):
    template_name = "accounts/password_change_done.html"


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
def change_mode(request):
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
        safe_next = request.session.pop(LOGIN_NEXT_SESSION_KEY, None)
        if safe_next and url_has_allowed_host_and_scheme(
            safe_next,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        ):
            return redirect(safe_next)
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


class ProfileDetailView(LoginRequiredMixin, DetailView):
    """Muestra únicamente el perfil del usuario autenticado."""

    model = User
    template_name = "accounts/profile_detail.html"
    context_object_name = "profile_user"

    def get_object(self, queryset=None):
        return (
            User.objects
            .prefetch_related(
                "groups",
                "terms_acceptances__terms_version",
            )
            .get(pk=self.request.user.pk)
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Permite editar solo los datos personales del usuario autenticado."""

    model = User
    form_class = ProfileUpdateForm
    template_name = "accounts/profile_form.html"
    context_object_name = "profile_user"

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse("accounts:profile")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            "Tu información personal se actualizó correctamente.",
        )
        return response


class UserListView(AdministratorModeRequiredMixin, ListView):
    model = User
    template_name = "accounts/user_list.html"
    context_object_name = "users"
    paginate_by = 15

    def get_queryset(self):
        queryset = (
            User.objects
            .prefetch_related("groups")
            .order_by("username")
        )
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query)
                | Q(email__icontains=query)
                | Q(document__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "").strip()
        return context


class UserDetailView(AdministratorModeRequiredMixin, DetailView):
    model = User
    template_name = "accounts/user_detail.html"
    context_object_name = "managed_user"

    def get_queryset(self):
        return (
            User.objects
            .select_related("vendor_profile")
            .prefetch_related(
                "groups",
                "terms_acceptances__terms_version",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        managed_user = context["managed_user"]
        context["has_vendor_role"] = managed_user.groups.filter(
            name=VENDOR
        ).exists()

        try:
            context["vendor_profile"] = managed_user.vendor_profile
        except ObjectDoesNotExist:
            context["vendor_profile"] = None

        return context


class CrudBootstrapFormMixin:
    """Aplica clases Bootstrap y restringe privilegios sensibles."""

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        # El panel visual administra roles de negocio. Los permisos
        # individuales y el superusuario permanecen en Django Admin.
        form.fields.pop("is_superuser", None)
        form.fields.pop("user_permissions", None)

        for field in form.fields.values():
            widget = field.widget
            current = widget.attrs.get("class", "").split()
            if getattr(widget, "input_type", None) == "checkbox":
                css_class = "form-check-input"
            elif (
                getattr(widget, "allow_multiple_selected", False)
                    or widget.__class__.__name__.endswith("Select")
                ):
                css_class = "form-select"
            else:
                css_class = "form-control"
            if css_class not in current:
                current.append(css_class)
            widget.attrs["class"] = " ".join(current)

        return form


class UserCreateView(CrudBootstrapFormMixin, AdministratorModeRequiredMixin, CreateView):
    model = User
    form_class = UserBusinessCreationForm
    template_name = "accounts/user_form.html"

    def get_success_url(self):
        return reverse(
            "accounts:user_detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Usuario {self.object.username} creado correctamente.",
        )
        return response


class UserUpdateView(CrudBootstrapFormMixin, AdministratorModeRequiredMixin, UpdateView):
    model = User
    form_class = UserBusinessChangeForm
    template_name = "accounts/user_form.html"
    context_object_name = "managed_user"

    def get_queryset(self):
        queryset = User.objects.all()
        if not self.request.user.is_superuser:
            queryset = queryset.filter(is_superuser=False)
        return queryset

    def get_success_url(self):
        return reverse(
            "accounts:user_detail",
            kwargs={"pk": self.object.pk},
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Usuario {self.object.username} actualizado correctamente.",
        )
        return response



class UserDeleteDeactivateView(
    AdministratorModeRequiredMixin,
    View,
):
    template_name = "accounts/user_confirm_delete.html"

    def get_object(self) -> User:
        return get_object_or_404(
            User,
            pk=self.kwargs["pk"],
        )

    def get(self, request, *args, **kwargs):
        managed_user = self.get_object()
        return render(
            request,
            self.template_name,
            {
                "managed_user": managed_user,
                "has_history": user_has_related_history(managed_user),
            },
        )

    def post(self, request, *args, **kwargs):
        managed_user = self.get_object()

        try:
            result = delete_or_deactivate_user(
                actor=request.user,
                target_id=managed_user.pk,
            )
        except ValidationError as exc:
            message = (
                exc.messages[0]
                if getattr(exc, "messages", None)
                else str(exc)
            )
            messages.error(request, message)
            return redirect(
                "accounts:user_detail",
                pk=managed_user.pk,
            )

        if result.action == "deactivated":
            messages.warning(
                request,
                (
                    f"El usuario {result.username} conserva historia "
                    "relacionada y fue desactivado sin eliminar sus "
                    "registros."
                ),
            )
        else:
            messages.success(
                request,
                (
                    f"El usuario {result.username} fue eliminado "
                    "físicamente porque no tenía historia."
                ),
            )

        return redirect("accounts:user_list")

