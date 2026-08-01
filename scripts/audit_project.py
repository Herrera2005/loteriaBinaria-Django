#!/usr/bin/env python3
"""Auditoría estática reproducible hasta P-28A del Taller #3.

No sustituye ``manage.py check`` ni la suite Django. Detecta fallos de
estructura, alcance, templates, seguridad básica y residuos del frontend
legado antes de ejecutar el proyecto con SQLite.
"""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ACTIVE_ROOTS = ("apps", "config", "templates", "static")
TEXT_SUFFIXES = {
    ".py",
    ".html",
    ".css",
    ".js",
    ".md",
    ".txt",
    ".ps1",
    ".sh",
}

REQUIRED_FILES = (
    "manage.py",
    "config/settings.py",
    "config/urls.py",
    "apps/accounts/models.py",
    "apps/accounts/forms.py",
    "apps/accounts/services.py",
    "apps/accounts/views.py",
    "apps/accounts/urls.py",
    "apps/vendors/models.py",
    "apps/vendors/forms.py",
    "apps/vendors/services.py",
    "apps/vendors/views.py",
    "apps/vendors/urls.py",
    "apps/vendors/migrations/0001_initial.py",
    "apps/vendors/tests/test_models.py",
    "apps/vendors/tests/test_views.py",
    "apps/lottery/models.py",
    "apps/lottery/forms.py",
    "apps/lottery/admin.py",
    "apps/lottery/services.py",
    "apps/lottery/views.py",
    "apps/lottery/urls.py",
    "apps/lottery/migrations/0001_initial.py",
    "apps/lottery/tests/test_models.py",
    "apps/lottery/tests/test_forms.py",
    "apps/lottery/tests/test_crud.py",
    "apps/core/context_processors.py",
    "apps/core/models.py",
    "apps/core/admin.py",
    "apps/core/migrations/0001_initial.py",
    "apps/core/tests/test_models.py",
    "apps/finance/models.py",
    "apps/finance/admin.py",
    "apps/finance/apps.py",
    "apps/finance/services.py",
    "apps/finance/signals.py",
    "apps/finance/migrations/0001_initial.py",
    "apps/finance/management/commands/backfill_wallets.py",
    "apps/finance/tests/test_models.py",
    "templates/base.html",
    "templates/includes/_messages.html",
    "templates/includes/_confirm_modal.html",
    "templates/vendors/vendorprofile_list.html",
    "templates/vendors/vendorprofile_detail.html",
    "templates/vendors/vendorprofile_form.html",
    "templates/vendors/vendorprofile_confirm_delete.html",
    "templates/vendors/conversionrequest_list.html",
    "templates/lottery/product_list.html",
    "templates/lottery/product_detail.html",
    "templates/lottery/product_form.html",
    "templates/lottery/product_confirm_delete.html",
    "templates/lottery/event_list.html",
    "templates/lottery/event_detail.html",
    "templates/lottery/event_form.html",
    "templates/lottery/event_confirm_delete.html",
    "static/css/app.css",
    "static/js/app.js",
    "static/img/logo-placeholder.png",
    "scripts/smoke_runserver.py",
    "scripts/verify.ps1",
    "docs/referencias/01_Reglas_Maestras_MVP_Django_v1.1.0.md",
    "docs/referencias/02_Plan_Tecnico_MVP_Django_v1.1.0.md",
    "docs/referencias/03_Matriz_Trazabilidad_Pruebas_MVP_Django_v1.1.0.md",
    "docs/referencias/04_Diseno_Interfaz_MVP_Django_v1.0.0.md",
    "docs/referencias/05_Auditoria_Coherencia_Interfaz_MVP_Django_v1.0.0.md",
    "docs/referencias/Manual_Intercalado_Taller_3_Loteria_Binaria_Django_v4.0.pdf",
    "respaldo_frontend/Proyecto_HerreraNietoCristhian_legacy.zip",
)

FORBIDDEN_PATTERNS = {
    "localStorage": re.compile(r"\blocalStorage\b"),
    "sessionStorage": re.compile(r"\bsessionStorage\b"),
    "fetch JSON": re.compile(r"\bfetch\s*\("),
    "usuarios.json": re.compile(r"usuarios\.json", re.I),
    "enlace pages/*.html": re.compile(
        r"(?:href|action)=[\"'][^\"']*pages/[^\"']+\.html",
        re.I,
    ),
    "CLIENTE_FINANCIERO": re.compile(r"CLIENTE_FINANCIERO"),
    "credencial demo heredada": re.compile(
        r"(?<![A-Za-z0-9])123456(?![A-Za-z0-9])"
    ),
    "porcentaje legado": re.compile(r"(?<!\d)(?:5|15|75)\s*%"),
}

EXPECTED_URL_NAMES = {
    "apps/vendors/urls.py": {
        "vendorprofile_list",
        "vendorprofile_create",
        "vendorprofile_detail",
        "vendorprofile_update",
        "vendorprofile_delete",
        "conversionrequest_list",
    },
    "apps/lottery/urls.py": {
        "product_list",
        "product_create",
        "product_detail",
        "product_update",
        "product_delete",
        "event_list",
        "event_create",
        "event_detail",
        "event_update",
        "event_delete",
    },
}

BINARY_SUFFIXES = {
    ".zip",
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".webp",
    ".sqlite3",
}


def tracked_relative_paths() -> list[Path]:
    """Usa Git cuando existe y permite auditar un ZIP limpio sin ``.git``."""

    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout:
        return [
            Path(item.decode("utf-8"))
            for item in result.stdout.split(b"\0")
            if item
        ]

    excluded_directories = {
        ".git",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "staticfiles",
    }
    relative_paths = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in excluded_directories for part in relative.parts):
            continue
        relative_paths.append(relative)
    return sorted(relative_paths, key=lambda item: item.as_posix())


def tracked_files() -> list[Path]:
    return [
        ROOT / relative
        for relative in tracked_relative_paths()
        if (ROOT / relative).is_file()
    ]


def iter_active_files():
    for path in tracked_files():
        relative = path.relative_to(ROOT)
        if (
            relative.parts
            and relative.parts[0] in ACTIVE_ROOTS
            and path.suffix.lower() in TEXT_SUFFIXES
        ):
            yield path


def check_required(errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"Falta archivo obligatorio: {relative}")


def check_python_syntax(errors: list[str]) -> None:
    for path in tracked_files():
        if path.suffix.lower() != ".py":
            continue
        try:
            ast.parse(
                path.read_text(encoding="utf-8"),
                filename=str(path),
            )
        except (SyntaxError, UnicodeDecodeError) as exc:
            errors.append(
                f"Python inválido en {path.relative_to(ROOT)}: {exc}"
            )


def check_generated_residue(errors: list[str]) -> None:
    for relative in tracked_relative_paths():
        relative_text = relative.as_posix()

        if "__pycache__" in relative.parts:
            errors.append(
                f"Directorio generado versionado: {relative_text}"
            )
        elif relative.suffix.lower() == ".pyc":
            errors.append(
                f"Bytecode generado versionado: {relative_text}"
            )

    for relative in (
        ".env",
        "db.sqlite3",
        "verification.sqlite3",
        "staticfiles",
    ):
        if relative in {
            path.as_posix()
            for path in tracked_relative_paths()
        }:
            errors.append(
                f"Artefacto local versionado y no entregable: {relative}"
            )


def check_forbidden(errors: list[str]) -> None:
    for path in iter_active_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(text):
                errors.append(
                    f"Residuo prohibido ({label}) en "
                    f"{path.relative_to(ROOT)}"
                )


def check_templates(errors: list[str]) -> None:
    template_root = ROOT / "templates"
    hashes: dict[str, list[Path]] = defaultdict(list)

    for path in template_root.rglob("*.html"):
        relative = path.relative_to(ROOT)
        text = path.read_text(encoding="utf-8")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        hashes[digest].append(path)

        if re.search(r"{%\s*\n", text):
            errors.append(
                f"Tag Django partido por salto de línea en {relative}"
            )

        is_partial = "includes" in path.parts
        is_base = relative.as_posix() == "templates/base.html"

        if not is_partial and not is_base:
            h1_count = len(
                re.findall(r"<h1\b", text, flags=re.I)
            )
            if h1_count != 1:
                errors.append(
                    f"{relative}: se esperaba 1 h1 y "
                    f"se encontraron {h1_count}"
                )
            if '{% extends "base.html" %}' not in text:
                errors.append(
                    f"{relative}: no extiende base.html"
                )
            if "{% load static %}" not in text:
                errors.append(
                    f"{relative}: no carga static"
                )

        for match in re.finditer(
            r"<form\b[^>]*method=[\"']post[\"'][^>]*>"
            r"(.*?)</form>",
            text,
            flags=re.I | re.S,
        ):
            if "{% csrf_token %}" not in match.group(1):
                errors.append(
                    f"Formulario POST sin CSRF en {relative}"
                )

    for paths in hashes.values():
        if len(paths) > 1:
            joined = ", ".join(
                str(path.relative_to(ROOT))
                for path in paths
            )
            errors.append(
                f"Templates duplicados byte a byte: {joined}"
            )

    base_path = template_root / "base.html"
    if base_path.is_file():
        base = base_path.read_text(encoding="utf-8")
        for expected in (
            "bootstrap@5.3",
            "navbar-expand",
            "offcanvas",
            "{% static 'css/app.css' %}",
            "{% static 'js/app.js' %}",
            "includes/_messages.html",
            "includes/_confirm_modal.html",
            "Simulación académica",
        ):
            if expected not in base:
                errors.append(
                    f"base.html no contiene: {expected}"
                )


def check_runtime_configuration(errors: list[str]) -> None:
    requirements = (
        ROOT / "requirements.txt"
    ).read_text(encoding="utf-8").lower()
    mysql_requirements = (
        ROOT / "requirements-mysql.txt"
    ).read_text(encoding="utf-8").lower()
    settings_text = (
        ROOT / "config/settings.py"
    ).read_text(encoding="utf-8").lower()
    env_example = (
        ROOT / ".env.example"
    ).read_text(encoding="utf-8").lower()

    for forbidden in ("psycopg", "psycopg-binary"):
        if (
            forbidden in requirements
            or forbidden in mysql_requirements
        ):
            errors.append(
                f"Dependencia runtime prohibida: {forbidden}"
            )

    if "django.db.backends.postgresql" in settings_text:
        errors.append(
            "Backend PostgreSQL prohibido en settings.py"
        )

    for label, text in (
        ("requirements.txt", requirements),
        ("requirements-mysql.txt", mysql_requirements),
        (".env.example", env_example),
    ):
        if "postgresql://" in text or "postgres://" in text:
            errors.append(
                f"URL PostgreSQL prohibida en {label}"
            )

    if "sqlite" not in settings_text or "mysql" not in settings_text:
        errors.append(
            "settings.py debe admitir SQLite y MySQL explícitamente"
        )


def check_scope_and_models(errors: list[str]) -> None:
    active_text = "\n".join(
        path.read_text(encoding="utf-8", errors="replace")
        for path in iter_active_files()
    )

    for forbidden in (
        "FloatField(",
        "ArrayField(",
        "JSONField(",
        "django.contrib.postgres",
        "celery",
        "redis",
        "rest_framework",
    ):
        if forbidden.lower() in active_text.lower():
            errors.append(
                f"Tecnología/campo fuera de alcance en runtime: "
                f"{forbidden}"
            )

    lottery_models = (
        ROOT / "apps/lottery/models.py"
    ).read_text(encoding="utf-8")

    for expected in (
        'OCTAL = "OCTAL"',
        'DECIMAL = "DECIMAL"',
        'HEXADECIMAL = "HEXADECIMAL"',
        '"allowed_symbols": "01234567"',
        '"selection_count": 4',
        '"allowed_symbols": "0123456789"',
        '"selection_count": 5',
        '"allowed_symbols": "0123456789ABCDEF"',
        '"selection_count": 6',
        "DRAW_CLOSE_OFFSET = timedelta(minutes=10)",
        "models.BigIntegerField",
        "models.OneToOneField",
        "on_delete=models.PROTECT",
        'fields=("event", "normalized_key")',
    ):
        if expected not in lottery_models:
            errors.append(
                "Regla Lottery no localizada en models.py: "
                f"{expected}"
            )

    forms = (
        ROOT / "apps/lottery/forms.py"
    ).read_text(encoding="utf-8")

    if (
        "class TicketForm" in forms
        or "class DrawResultForm" in forms
    ):
        errors.append(
            "Ticket/DrawResult no deben tener ModelForm genérico"
        )

    services = (
        ROOT / "apps/lottery/services.py"
    ).read_text(encoding="utf-8")

    if services.count("@transaction.atomic") < 2:
        errors.append(
            "Las dos eliminaciones Lottery deben ser "
            "transaccionales"
        )



def check_p28a_models(errors: list[str]) -> None:
    finance_models = (
        ROOT / "apps/finance/models.py"
    ).read_text(encoding="utf-8")
    core_models = (
        ROOT / "apps/core/models.py"
    ).read_text(encoding="utf-8")
    finance_services = (
        ROOT / "apps/finance/services.py"
    ).read_text(encoding="utf-8")

    for expected in (
        "class Wallet(models.Model)",
        "class Movement(models.Model)",
        "available_minor = models.BigIntegerField",
        "reserved_minor = models.BigIntegerField",
        "amount_minor = models.BigIntegerField",
        "balance_after_minor = models.BigIntegerField",
        "fin_wallet_user_curr_uq",
        "on_delete=models.PROTECT",
        "HistoricalMovementQuerySet",
    ):
        if expected not in finance_models:
            errors.append(
                f"Regla P-28A Finance no localizada: {expected}"
            )

    for expected in (
        "@transaction.atomic",
        "def ensure_user_wallets",
        "Wallet.Currency.REAL",
        "Wallet.Currency.VIRTUAL",
        "get_or_create",
    ):
        if expected not in finance_services:
            errors.append(
                f"Servicio P-28A no localizado: {expected}"
            )

    for expected in (
        "class AuditEvent(models.Model)",
        "HistoricalAuditQuerySet",
        "on_delete=models.PROTECT",
        "resource_type",
        "resource_id",
        "metadata = models.TextField",
    ):
        if expected not in core_models:
            errors.append(
                f"Regla P-28A AuditEvent no localizada: {expected}"
            )

    for forbidden in (
        "models.FloatField(",
        "models.DecimalField(",
        "models.JSONField(",
    ):
        if forbidden in finance_models or forbidden in core_models:
            errors.append(
                f"Campo prohibido en P-28A: {forbidden}"
            )

def check_urls(errors: list[str]) -> None:
    config_urls = (
        ROOT / "config/urls.py"
    ).read_text(encoding="utf-8")

    for include_path in (
        "apps.accounts.urls",
        "apps.core.urls",
        "apps.vendors.urls",
        "apps.lottery.urls",
    ):
        if include_path not in config_urls:
            errors.append(
                f"config/urls.py no integra {include_path}"
            )

    for relative, expected_names in EXPECTED_URL_NAMES.items():
        text = (
            ROOT / relative
        ).read_text(encoding="utf-8")

        for name in expected_names:
            if f'name="{name}"' not in text:
                errors.append(
                    f"Falta URL name={name} en {relative}"
                )


def check_legacy_runtime(errors: list[str]) -> None:
    for relative in ("index.html", "pages"):
        if (ROOT / relative).exists():
            errors.append(
                "Ruta legado activa en raíz; debe vivir solo "
                f"en respaldo: {relative}"
            )


def check_text_controls(errors: list[str]) -> None:
    for path in tracked_files():
        if path.suffix.lower() in BINARY_SUFFIXES:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue

        data = path.read_bytes()
        controls = sorted(
            {
                byte
                for byte in data
                if byte < 32 and byte not in (9, 10, 13)
            }
        )

        if controls:
            errors.append(
                f"Caracteres de control en "
                f"{path.relative_to(ROOT)}: {controls}"
            )


def check_test_inventory(errors: list[str]) -> int:
    test_count = 0

    for path in ROOT.glob("apps/*/tests/test_*.py"):
        tree = ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
        )
        test_count += sum(
            1
            for node in ast.walk(tree)
            if isinstance(
                node,
                (ast.FunctionDef, ast.AsyncFunctionDef),
            )
            and node.name.startswith("test_")
        )

    if test_count < 160:
        errors.append(
            "Inventario insuficiente para el estado P-27: "
            f"{test_count}; se esperaban al menos 160 pruebas "
            "diseñadas"
        )

    return test_count


def main() -> int:
    errors: list[str] = []

    try:
        check_required(errors)
        check_python_syntax(errors)
        check_generated_residue(errors)
        check_forbidden(errors)
        check_templates(errors)
        check_runtime_configuration(errors)
        check_scope_and_models(errors)
        check_p28a_models(errors)
        check_urls(errors)
        check_legacy_runtime(errors)
        check_text_controls(errors)
        test_count = check_test_inventory(errors)
    except RuntimeError as exc:
        print(f"AUDITORÍA ESTÁTICA P-28A: FALLÓ\n- {exc}")
        return 1

    if errors:
        print("AUDITORÍA ESTÁTICA P-28A: FALLÓ")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AUDITORÍA ESTÁTICA P-28A: OK")
    print("- Estructura Accounts/Vendors/Lottery/Finance/Core presente")
    print("- Python parseable y sin bytecode versionado")
    print("- Templates base, H1, CSRF y duplicados verificados")
    print("- URLs de Vendors y Lottery integradas")
    print("- Sin localStorage, JSON de negocio ni pages/*.html activos")
    print("- SQLite/MySQL permitidos y PostgreSQL excluido")
    print(
        "- Reglas 4/5/6, cierre 10 min, wallets e históricos "
        "protegidos localizados"
    )
    print(
        f"- {test_count} pruebas automatizadas diseñadas"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())