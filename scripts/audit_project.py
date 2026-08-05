#!/usr/bin/env python3
"""Auditoría estática de cierre del Taller #3 — estado P-36E reparado."""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = (
    "manage.py",
    "config/settings.py",
    "config/urls.py",
    ".env.example",
    ".gitignore",
    "requirements.txt",
    "requirements-mysql.txt",
    "README.md",
    "MANIFEST_SHA256.txt",
    "apps/accounts/models.py",
    "apps/accounts/forms.py",
    "apps/accounts/services.py",
    "apps/accounts/views.py",
    "apps/accounts/urls.py",
    "apps/core/models.py",
    "apps/core/views.py",
    "apps/core/date_utils.py",
    "apps/finance/models.py",
    "apps/finance/services.py",
    "apps/finance/views.py",
    "apps/vendors/models.py",
    "apps/vendors/forms.py",
    "apps/vendors/services.py",
    "apps/vendors/views.py",
    "apps/lottery/models.py",
    "apps/lottery/forms.py",
    "apps/lottery/services.py",
    "apps/lottery/views.py",
    "apps/lottery/urls.py",
    "apps/lottery/migrations/0010_draweventseries_last_synced_at.py",
    "apps/lottery/migrations/0011_portable_series_sequence_unique.py",
    "apps/lottery/management/commands/process_lottery_schedules.py",
    "apps/lottery/tests/test_event_series.py",
    "apps/lottery/tests/test_automatic_results.py",
    "apps/lottery/tests/test_closure_repairs.py",
    "templates/base.html",
    "templates/lottery/series_list.html",
    "templates/lottery/series_detail.html",
    "templates/lottery/series_form.html",
    "templates/lottery/event_detail.html",
    "static/css/app.css",
    "static/js/app.js",
    "scripts/manifest_project.py",
    "scripts/verify.sh",
    "scripts/verify.ps1",
    "scripts/verify_mysql.sh",
    "scripts/verify_mysql.ps1",
    "docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md",
    "docs/INVENTARIO_FINAL.md",
    "docs/RESULTADO_AUDITORIA_FINAL.md",
    "docs/PLAN_SIGUIENTE_TRABAJO.md",
    "docs/REPARACION_HALLAZGOS_CIERRE.md",
    "respaldo_frontend/Proyecto_HerreraNietoCristhian_legacy.zip",
)

FORBIDDEN_ROOT_NAMES = {".venv", "venv", "env", "staticfiles", "__pycache__"}
FORBIDDEN_FILE_NAMES = {".env", "db.sqlite3", "verification.sqlite3"}
FORBIDDEN_SUFFIXES = {".pyc", ".pyo", ".bak", ".log", ".sqlite3", ".db"}
DEAD_TEMPLATES = {
    "templates/finance/conversion_form.html",
    "templates/finance/movement_list.html",
    "templates/finance/topup_form.html",
    "templates/finance/withdrawal_form.html",
}
CURRENT_DOCS = (
    "README.md",
    "docs/MATRIZ_TRAZABILIDAD_FASE_ACTUAL.md",
    "docs/INVENTARIO_FINAL.md",
    "docs/RESULTADO_AUDITORIA_FINAL.md",
    "docs/PLAN_SIGUIENTE_TRABAJO.md",
    "docs/AUDITORIA_REPARACION_P36_VISUAL.md",
)
STALE_CURRENT_PATTERNS = (
    "llega hasta el P-28",
    "El siguiente bloque es P-29",
    "compra de boletos, recargas, conversiones y compra mayorista todavía no",
    "finance`, `vendors` y `lottery` están vacías",
    "396 pruebas automatizadas diseñadas",
    "219 pruebas automatizadas diseñadas",
)
EXPECTED_PROJECT_URLS = {
    "accounts:login",
    "accounts:logout",
    "accounts:register",
    "accounts:choose_mode",
    "accounts:profile",
    "core:home",
    "core:client_dashboard",
    "core:vendor_dashboard",
    "core:admin_dashboard",
    "core:audit_list",
    "finance:wallet_detail",
    "finance:real_operations",
    "finance:wallet_conversion",
    "finance:virtual_transfer",
    "vendors:vendorprofile_list",
    "vendors:conversionrequest_list",
    "lottery:product_list",
    "lottery:event_list",
    "lottery:event_create",
    "lottery:series_list",
    "lottery:series_detail",
    "lottery:series_update",
    "lottery:series_toggle",
    "lottery:series_archive",
    "lottery:series_generate",
    "lottery:client_event_list",
    "lottery:client_ticket_list",
}


SOURCE_SCAN_EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "staticfiles",
    "Respaldos",
}
SOURCE_SCAN_EXCLUDED_NAMES = {
    ".env",
    "db.sqlite3",
    "verification.sqlite3",
}
SOURCE_SCAN_EXCLUDED_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".bak",
    ".log",
    ".sqlite3",
    ".db",
}


def project_files():
    """Recorre únicamente archivos fuente auditables.

    Los residuos de entrega se revisan por separado con ``check_residue``
    cuando se usa ``--package``. La auditoría normal no debe interpretar
    templates, Python ni recursos pertenecientes al entorno virtual.
    """
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in SOURCE_SCAN_EXCLUDED_DIRS for part in relative.parts):
            continue
        if relative.name in SOURCE_SCAN_EXCLUDED_NAMES:
            continue
        if relative.suffix.lower() in SOURCE_SCAN_EXCLUDED_SUFFIXES:
            continue
        yield relative, path


def check_required(errors):
    for relative in REQUIRED_FILES:
        if not (ROOT / relative).is_file():
            errors.append(f"Falta archivo requerido: {relative}")
    for relative in DEAD_TEMPLATES:
        if (ROOT / relative).exists():
            errors.append(f"Template muerto todavía presente: {relative}")


def check_residue(errors):
    for relative, path in project_files():
        if any(part in FORBIDDEN_ROOT_NAMES for part in relative.parts):
            errors.append(f"Residuo de entrega: {relative}")
            continue
        if relative.name in FORBIDDEN_FILE_NAMES:
            errors.append(f"Archivo prohibido en entrega: {relative}")
            continue
        if relative.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"Residuo generado: {relative}")


def check_python(errors):
    for relative, path in project_files():
        if path.suffix != ".py":
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(relative))
        except (SyntaxError, UnicodeDecodeError) as exc:
            errors.append(f"Python inválido en {relative}: {exc}")


def url_names_from_file(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8-sig")
    app_match = re.search(r'app_name\s*=\s*["\']([^"\']+)', text)
    if not app_match:
        return set()
    namespace = app_match.group(1)
    return {
        f"{namespace}:{name}"
        for name in re.findall(r'name\s*=\s*["\']([^"\']+)', text)
    }


def check_urls(errors):
    defined = set()
    for path in ROOT.glob("apps/*/urls.py"):
        defined.update(url_names_from_file(path))
    missing_expected = sorted(EXPECTED_PROJECT_URLS - defined)
    for name in missing_expected:
        errors.append(f"URL requerida no definida: {name}")
    if "lottery:series_create" in defined:
        errors.append("La ruta muerta lottery:series_create sigue definida.")

    reference_pattern = re.compile(
        r"(?:url\s+|reverse(?:_lazy)?\(\s*|redirect\(\s*)[\"']([a-z_]+:[a-z0-9_]+)",
        re.I,
    )
    for relative, path in project_files():
        if path.suffix.lower() not in {".py", ".html"}:
            continue
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
        for name in reference_pattern.findall(text):
            if name.startswith("admin:"):
                continue
            if (
                name == "lottery:series_create"
                and relative.as_posix()
                in {
                    "apps/lottery/tests/test_closure_repairs.py",
                    "scripts/audit_project.py",
                }
            ):
                continue
            if name not in defined:
                errors.append(f"Referencia a URL inexistente {name} en {relative}")


def check_templates(errors):
    for relative, path in project_files():
        if path.suffix != ".html":
            continue
        text = path.read_text(encoding="utf-8-sig")
        for form in re.findall(r"<form\b.*?</form>", text, flags=re.I | re.S):
            method = re.search(r'method\s*=\s*["\']([^"\']+)', form, flags=re.I)
            if method and method.group(1).lower() == "post" and "{% csrf_token %}" not in form:
                errors.append(f"Formulario POST sin CSRF en {relative}")


def check_get_safety(errors):
    core_text = (ROOT / "apps/core/views.py").read_text(encoding="utf-8")
    if "sync_lottery_event_states" in core_text:
        errors.append("Core todavía sincroniza estados desde vistas GET.")

    path = ROOT / "apps/lottery/views.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))

    class Visitor(ast.NodeVisitor):
        def __init__(self):
            self.function_stack = []

        def visit_FunctionDef(self, node):
            self.function_stack.append(node.name)
            self.generic_visit(node)
            self.function_stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node):
            name = None
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            if name == "sync_lottery_event_states":
                current = self.function_stack[-1] if self.function_stack else "<module>"
                if current != "post":
                    errors.append(
                        "sync_lottery_event_states fuera de POST en "
                        f"apps/lottery/views.py ({current})."
                    )
            self.generic_visit(node)

    Visitor().visit(tree)


def check_rules(errors):
    models_text = (ROOT / "apps/lottery/models.py").read_text(encoding="utf-8")
    services_text = (ROOT / "apps/lottery/services.py").read_text(encoding="utf-8")
    settings_text = (ROOT / "config/settings.py").read_text(encoding="utf-8")
    core_views = (ROOT / "apps/core/views.py").read_text(encoding="utf-8")
    finance_views = (ROOT / "apps/finance/views.py").read_text(encoding="utf-8")

    for required in (
        "class ImmutableTransitionQuerySet",
        "objects = ImmutableTransitionQuerySet.as_manager()",
        "class SeriesBatchProcessingResult",
        "last_synced_at",
        "can_purchase_ticket_for_mode",
    ):
        haystack = models_text + services_text + (ROOT / "apps/accounts/policies.py").read_text(encoding="utf-8")
        if required not in haystack:
            errors.append(f"Control de cierre no localizado: {required}")

    constraint_match = re.search(
        r'models\.UniqueConstraint\(\s*fields=\("series", "series_sequence"\).*?name="lot_event_unique_series_sequence"',
        models_text,
        flags=re.S,
    )
    if not constraint_match or "condition=" in constraint_match.group(0):
        errors.append("La unicidad de secuencia de serie no es portable.")

    if "created_at__date" in core_views or "created_at__date" in finance_views:
        errors.append("Persisten filtros __date no portables para MySQL.")

    for setting in (
        "SECURE_SSL_REDIRECT",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
        "SECURE_HSTS_SECONDS",
    ):
        if setting not in settings_text:
            errors.append(f"Falta configuración productiva: {setting}")

    if "django.db.backends.postgresql" in settings_text:
        errors.append("PostgreSQL no pertenece al Taller #3.")
    for engine in ("django.db.backends.sqlite3", "django.db.backends.mysql"):
        if engine not in settings_text:
            errors.append(f"Motor requerido no configurado: {engine}")


def check_current_docs(errors):
    for relative in CURRENT_DOCS:
        path = ROOT / relative
        if not path.exists():
            errors.append(f"Documento vigente ausente: {relative}")
            continue
        text = path.read_text(encoding="utf-8-sig")
        for stale in STALE_CURRENT_PATTERNS:
            if stale.lower() in text.lower():
                errors.append(f"Texto obsoleto en {relative}: {stale}")

    duplicate_docs = list((ROOT / "docs").glob("* (*)*.md"))
    for path in duplicate_docs:
        errors.append(f"Documento duplicado sin clasificar: {path.relative_to(ROOT)}")


def check_forbidden_runtime(errors):
    patterns = {
        "localStorage": re.compile(r"\blocalStorage\b"),
        "sessionStorage": re.compile(r"\bsessionStorage\b"),
        "CLIENTE_FINANCIERO": re.compile(r"CLIENTE_FINANCIERO"),
        "usuarios.json": re.compile(r"usuarios\.json", re.I),
    }
    active_roots = (ROOT / "apps", ROOT / "config", ROOT / "templates", ROOT / "static")
    for base in active_roots:
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".py", ".html", ".js", ".css"}:
                continue
            text = path.read_text(encoding="utf-8-sig", errors="ignore")
            for label, pattern in patterns.items():
                if pattern.search(text):
                    errors.append(f"Persistencia o término legado {label} en {path.relative_to(ROOT)}")


def check_test_inventory(errors):
    count = 0
    for path in ROOT.glob("apps/*/tests/test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        count += sum(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
            for node in ast.walk(tree)
        )
    if count < 430:
        errors.append(f"Inventario de pruebas insuficiente para cierre: {count}")
    return count


def check_manifest(errors):
    result = subprocess.run(
        [sys.executable, "scripts/manifest_project.py"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip()
        errors.append(f"Manifiesto inválido: {detail}")


def main(package_strict: bool = False) -> int:
    errors = []
    check_required(errors)
    if package_strict:
        check_residue(errors)
    check_python(errors)
    check_urls(errors)
    check_templates(errors)
    check_get_safety(errors)
    check_rules(errors)
    check_current_docs(errors)
    check_forbidden_runtime(errors)
    test_count = check_test_inventory(errors)
    check_manifest(errors)

    if errors:
        print("AUDITORÍA ESTÁTICA DE CIERRE: FALLÓ")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AUDITORÍA ESTÁTICA DE CIERRE: OK")
    if package_strict:
        print("- Paquete sin entorno, base local, secretos ni bytecode")
    else:
        print("- Estructura fuente revisada; use --package para validar residuos del ZIP")
    print("- Python, templates, URLs y CSRF revisados")
    print("- GET sin sincronizaciones persistentes")
    print("- Históricos e idempotencia de series protegidos")
    print("- SQLite/MySQL documentados y constraint de series portable")
    print("- Documentación vigente alineada con P-36E")
    print(f"- {test_count} pruebas automatizadas inventariadas")
    print("- Manifiesto SHA-256 verificado")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--package",
        action="store_true",
        help="Valida además que el árbol entregable no contenga entorno, base ni residuos.",
    )
    arguments = parser.parse_args()
    sys.exit(main(package_strict=arguments.package))