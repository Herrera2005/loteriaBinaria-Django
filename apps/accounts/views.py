"""Vistas de autenticación, registro, modo y CRUD administrativo de usuarios."""

from __future__ import annotations

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    redirect_to_login,
)
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views.decorators.http import require_http_methods
from django.views.generic import CreateView, DetailView, ListView, UpdateView, View


from .access import (
    ACTIVE_MODE_SESSION_KEY,
    assigned_mode_codes,
    get_valid_active_mode,
)
from .forms import (
    ModeSelectionForm,
    RegistrationForm,
    TallerAuthenticationForm,
    UserAdminChangeForm,
    UserAdminCreationForm,
)
from .models import User
from .roles import (
    ADMINISTRATOR,
    DASHBOARD_URL_NAMES,
    ROLE_PRESENTATION,
)


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


class AdministratorModeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige cuenta activa, staff, rol y modo ADMINISTRADOR vigente."""

    raise_exception = True

    def test_func(self) -> bool:
        user = self.request.user
        if not user.is_authenticated:
            return False
        return (
            user.is_active
            and user.status == User.Status.ACTIVE
            and user.is_staff
            and ADMINISTRATOR in assigned_mode_codes(user)
            and get_valid_active_mode(self.request) == ADMINISTRATOR
        )
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )

        raise PermissionDenied(
            "Se requiere una cuenta administrativa activa y el modo "
            "ADMINISTRADOR."
        )


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
        return User.objects.prefetch_related(
            "groups",
            "terms_acceptances__terms_version",
        )


class CrudBootstrapFormMixin:
    """Aplica clases Bootstrap y restringe privilegios sensibles."""

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if not self.request.user.is_superuser:
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
    form_class = UserAdminCreationForm
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
    form_class = UserAdminChangeForm
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


def _has_related_history(user: User) -> bool:
    """Detecta relaciones históricas reales sin acoplarse a apps futuras."""
    for relation in user._meta.related_objects:
        if relation.many_to_many:
            continue

        accessor_name = relation.get_accessor_name()

        if relation.one_to_one:
            try:
                getattr(user, accessor_name)
            except relation.related_model.DoesNotExist:
                continue
            return True

        related_manager = getattr(user, accessor_name, None)
        if related_manager is not None and related_manager.exists():
            return True

    return False


def _deactivate_user(user: User) -> None:
    user.status = User.Status.DISABLED
    user.is_active = False
    user.save(
        update_fields=(
            "status",
            "is_active",
            "updated_at",
        )
    )


class UserDeleteDeactivateView(
    AdministratorModeRequiredMixin,
    View,
):
    template_name = "accounts/user_confirm_delete.html"

    def get_object(self) -> User:
        return User.objects.get(pk=self.kwargs["pk"])

    def get(self, request, *args, **kwargs):
        managed_user = self.get_object()
        return render(
            request,
            self.template_name,
            {
                "managed_user": managed_user,
                "has_history": _has_related_history(managed_user),
            },
        )

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        managed_user = (
            User.objects
            .select_for_update()
            .get(pk=self.kwargs["pk"])
        )

        if managed_user.pk == request.user.pk:
            messages.error(
                request,
                "No puedes eliminar ni desactivar tu propia cuenta desde esta operación.",
            )
            return redirect(
                "accounts:user_detail",
                pk=managed_user.pk,
            )

        if managed_user.is_superuser:
            messages.error(
                request,
                "Los superusuarios no se eliminan ni desactivan desde este CRUD.",
            )
            return redirect(
                "accounts:user_detail",
                pk=managed_user.pk,
            )

        if _has_related_history(managed_user):
            _deactivate_user(managed_user)
            messages.warning(
                request,
                (
                    f"El usuario {managed_user.username} conserva historia "
                    "relacionada y fue desactivado sin eliminar sus registros."
                ),
            )
        else:
            username = managed_user.username
            try:
                managed_user.delete()
            except ProtectedError:
                _deactivate_user(managed_user)
                messages.warning(
                    request,
                    (
                        f"El usuario {username} recibió historia relacionada "
                        "durante la operación y fue desactivado sin eliminarla."
                    ),
                )
            else:
                messages.success(
                    request,
                    (
                        f"El usuario {username} fue eliminado físicamente "
                        "porque no tenía historia."
                    ),
                )

        return redirect("accounts:user_list")
