#!/usr/bin/env python3
"""Auditoría estática reproducible del Taller #3.

No sustituye `manage.py check` ni la suite Django. Sirve para detectar
errores de estructura, residuos del frontend legado y templates rotos.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ACTIVE_ROOTS = ("apps", "config", "templates", "static")
REQUIRED_FILES = (
    "manage.py",
    "config/settings.py",
    "config/urls.py",
    "apps/accounts/models.py",
    "apps/accounts/forms.py",
    "apps/accounts/services.py",
    "apps/accounts/views.py",
    "apps/accounts/tests/test_model_integrity.py",
    "apps/core/tests/test_configuration.py",
    "apps/accounts/urls.py",
    "apps/core/views.py",
    "apps/core/urls.py",
    "templates/base.html",
    "templates/includes/_messages.html",
    "static/css/app.css",
    "static/js/app.js",
    "scripts/smoke_runserver.py",
    "docs/ESCALABILIDAD_MANUAL_V4.md",
    "docs/VERIFICACION_RUNSERVER.md",
    "static/img/logo-placeholder.png",
    "docs/INFORME_AUDITORIA_INTEGRAL.md",
    "docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md",
    "respaldo_frontend/Proyecto_HerreraNietoCristhian_legacy.zip",
)
FORBIDDEN_PATTERNS = {
    "localStorage": re.compile(r"\blocalStorage\b"),
    "sessionStorage": re.compile(r"\bsessionStorage\b"),
    "fetch JSON": re.compile(r"\bfetch\s*\("),
    "usuarios.json": re.compile(r"usuarios\.json", re.I),
    "enlace pages/*.html": re.compile(r"(?:href|action)=[\"'][^\"']*pages/[^\"']+\.html", re.I),
    "CLIENTE_FINANCIERO": re.compile(r"CLIENTE_FINANCIERO"),
    "credencial demo heredada": re.compile(r"(?<![A-Za-z0-9])123456(?![A-Za-z0-9])"),
    "porcentaje legado": re.compile(r"(?<!\d)(?:5|15|75)\s*%"),
}
LEAF_TEMPLATES = (
    "templates/403.html",
    "templates/404.html",
    "templates/core/home.html",
    "templates/accounts/login.html",
    "templates/accounts/register.html",
    "templates/accounts/choose_mode.html",
    "templates/dashboards/client.html",
    "templates/dashboards/vendor.html",
    "templates/dashboards/admin.html",
)


def iter_active_files():
    for root_name in ACTIVE_ROOTS:
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".py", ".html", ".css", ".js"}:
                yield path


def check_required(errors: list[str]) -> None:
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"Falta archivo obligatorio: {relative}")


def check_python_syntax(errors: list[str]) -> None:
    for path in ROOT.rglob("*.py"):
        if any(part in {".venv", "venv", "__pycache__"} for part in path.parts):
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            errors.append(f"Python inválido en {path.relative_to(ROOT)}: {exc}")


def check_forbidden(errors: list[str]) -> None:
    for path in iter_active_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in FORBIDDEN_PATTERNS.items():
            if pattern.search(text):
                errors.append(
                    f"Residuo prohibido ({label}) en {path.relative_to(ROOT)}"
                )


def check_templates(errors: list[str]) -> None:
    for relative in LEAF_TEMPLATES:
        path = ROOT / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        h1_count = len(re.findall(r"<h1\b", text, flags=re.I))
        if h1_count != 1:
            errors.append(f"{relative}: se esperaba 1 h1 y se encontraron {h1_count}")
        if relative not in {"templates/403.html", "templates/404.html"} and '{% extends "base.html" %}' not in text:
            errors.append(f"{relative}: no extiende base.html")

    for path in (ROOT / "templates").rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        # Aproximación deliberadamente conservadora: cualquier form POST debe
        # contener CSRF en su propio bloque hasta </form>.
        for match in re.finditer(r"<form\b[^>]*method=[\"']post[\"'][^>]*>(.*?)</form>", text, flags=re.I | re.S):
            if "{% csrf_token %}" not in match.group(1):
                errors.append(
                    f"Formulario POST sin CSRF en {path.relative_to(ROOT)}"
                )

    base = (ROOT / "templates/base.html").read_text(encoding="utf-8")
    for expected in (
        "{% static 'css/app.css' %}",
        "{% static 'js/app.js' %}",
        'includes/_messages.html',
    ):
        if expected not in base:
            errors.append(f"base.html no contiene: {expected}")


def check_legacy_runtime(errors: list[str]) -> None:
    for relative in ("index.html", "pages"):
        if (ROOT / relative).exists():
            errors.append(
                f"Ruta legado activa en raíz; debe vivir solo en el ZIP de respaldo: {relative}"
            )
    if (ROOT / "static/app.css").exists():
        errors.append("CSS mal ubicado: static/app.css; debe ser static/css/app.css")
    if (ROOT / "templates/includes/_manages.html").exists():
        errors.append("Partial con typo: _manages.html; debe ser _messages.html")


def check_runtime_configuration(errors: list[str]) -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").lower()
    mysql_requirements = (ROOT / "requirements-mysql.txt").read_text(encoding="utf-8").lower()
    settings_text = (ROOT / "config/settings.py").read_text(encoding="utf-8").lower()
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8").lower()

    # Es válido documentar que PostgreSQL está prohibido. Lo que no puede
    # aparecer es una dependencia, URL o backend ejecutable de PostgreSQL.
    for forbidden in ("psycopg", "psycopg-binary"):
        if forbidden in requirements or forbidden in mysql_requirements:
            errors.append(
                f"Dependencia runtime prohibida para Taller #3: {forbidden}"
            )

    if "django.db.backends.postgresql" in settings_text:
        errors.append(
            "Backend runtime prohibido para Taller #3: django.db.backends.postgresql"
        )

    for label, text in (
        ("requirements.txt", requirements),
        ("requirements-mysql.txt", mysql_requirements),
        (".env.example", env_example),
    ):
        if "postgresql://" in text or "postgres://" in text:
            errors.append(f"URL PostgreSQL prohibida en {label}")


def check_text_controls(errors: list[str]) -> None:
    ignored_suffixes = {".zip", ".pdf", ".png", ".jpg", ".jpeg", ".webp"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() in ignored_suffixes:
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        data = path.read_bytes()
        controls = sorted(set(byte for byte in data if byte < 32 and byte not in (9, 10, 13)))
        if controls:
            errors.append(
                f"Caracteres de control en {path.relative_to(ROOT)}: {controls}"
            )


def check_test_inventory(errors: list[str]) -> None:
    test_count = 0
    for path in ROOT.glob("apps/*/tests/test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        test_count += sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        )
    if test_count < 48:
        errors.append(f"Cobertura diseñada insuficiente: {test_count} pruebas; se esperaban al menos 48")


def main() -> int:
    errors: list[str] = []
    check_required(errors)
    check_python_syntax(errors)
    check_forbidden(errors)
    check_templates(errors)
    check_legacy_runtime(errors)
    check_runtime_configuration(errors)
    check_text_controls(errors)
    check_test_inventory(errors)

    if errors:
        print("AUDITORÍA ESTÁTICA: FALLÓ")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AUDITORÍA ESTÁTICA: OK")
    print("- Estructura mínima presente")
    print("- Python parseable")
    print("- Templates base/H1/CSRF verificados")
    print("- Sin localStorage, fetch JSON, credenciales demo ni pages/*.html activos")
    print("- ZIP visual legado preservado fuera del runtime")
    print("- Configuración sin PostgreSQL y 48 pruebas diseñadas")
    return 0


if __name__ == "__main__":
    sys.exit(main())
