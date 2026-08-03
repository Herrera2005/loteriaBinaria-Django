from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.urls import reverse


ROOT = Path(settings.BASE_DIR)


class UXAccessibilityClosureTests(TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_base_uses_bootstrap_53_and_accessible_navigation(self):
        source = self.read("templates/base.html")
        self.assertIn("bootstrap@5.3.8", source)
        self.assertIn('name="viewport"', source)
        self.assertIn('class="visually-hidden-focusable skip-link"', source)
        self.assertIn('aria-label="Navegación del modo activo"', source)
        self.assertIn('aria-controls="mainNavigation"', source)

    def test_confirmation_modal_has_explicit_dialog_semantics_and_safe_focus(self):
        modal = self.read("templates/includes/_confirm_modal.html")
        script = self.read("static/js/app.js")
        self.assertIn('role="dialog"', modal)
        self.assertIn('aria-modal="true"', modal)
        self.assertIn('id="confirmationModalCancel"', modal)
        self.assertIn("modalCancel || modalAccept", script)
        self.assertIn("Confirmar acción sensible", script)

    def test_messages_expose_status_and_error_prefixes(self):
        source = self.read("templates/includes/_messages.html")
        self.assertIn('aria-live="polite"', source)
        self.assertIn("Error:", source)
        self.assertIn("Correcto:", source)
        self.assertIn("Atención:", source)

    def test_responsive_tables_have_static_accessible_names(self):
        templates = (
            "templates/accounts/user_list.html",
            "templates/core/audit_list.html",
            "templates/finance/wallet_detail.html",
            "templates/lottery/event_list.html",
            "templates/lottery/series_list.html",
            "templates/vendors/vendorprofile_list.html",
        )
        for template in templates:
            with self.subTest(template=template):
                source = self.read(template)
                self.assertIn("data-table-label=", source)
                self.assertIn("table-responsive", source)

    def test_filter_forms_have_search_landmark(self):
        templates = (
            "templates/accounts/user_list.html",
            "templates/core/audit_list.html",
            "templates/lottery/client_event_list.html",
            "templates/lottery/event_list.html",
            "templates/lottery/series_list.html",
            "templates/vendors/vendorprofile_list.html",
        )
        for template in templates:
            with self.subTest(template=template):
                source = self.read(template)
                self.assertIn('role="search"', source)
                self.assertIn('aria-label="Filtrar resultados"', source)

    def test_event_availability_does_not_depend_only_on_color(self):
        for template in (
            "templates/dashboards/client.html",
            "templates/lottery/client_event_list.html",
            "templates/lottery/client_event_detail.html",
        ):
            with self.subTest(template=template):
                source = self.read(template)
                self.assertIn("status-badge--open", source)
                self.assertIn("Ventas abiertas", source)
                self.assertIn("status-badge--upcoming", source)
                self.assertIn("Próximamente", source)
                self.assertIn("Estado: ", source)

    def test_css_covers_required_breakpoints_focus_touch_and_reduced_motion(self):
        source = self.read("static/css/app.css")
        self.assertIn("@media (max-width: 575.98px)", source)
        self.assertIn("@media (min-width: 1200px)", source)
        self.assertIn("prefers-reduced-motion", source)
        self.assertIn(":focus-visible", source)
        self.assertIn("min-height: 2.75rem", source)
        self.assertIn("font-size: 1rem", source)
        self.assertIn("status-badge--open", source)
        self.assertIn("status-badge--upcoming", source)

    def test_table_enhancement_is_named_focusable_and_idempotent(self):
        source = self.read("static/js/app.js")
        self.assertIn('region.setAttribute("role", "region")', source)
        self.assertIn("region.tabIndex = 0", source)
        self.assertIn("region.dataset.tableLabel", source)
        self.assertIn("if (!hint)", source)

    def test_error_pages_offer_two_recovery_paths(self):
        for name in ("403.html", "404.html"):
            source = self.read(f"templates/{name}")
            self.assertIn("data-history-back", source)
            self.assertIn("Ir al inicio seguro", source)

    def test_public_pages_render_with_expected_accessibility_hooks(self):
        for url_name, expected in (
            ("core:home", "Simulación académica"),
            ("accounts:login", "Iniciar sesión"),
            ("accounts:register", "Crear cuenta"),
        ):
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected)
                self.assertContains(response, "Saltar al contenido principal")

    def test_templates_do_not_claim_ticket_purchase_is_unavailable(self):
        forbidden = (
            "todavía no se compra",
            "compra de boletos todavía no",
            "resultados no existen",
        )
        for path in (ROOT / "templates").rglob("*.html"):
            source = path.read_text(encoding="utf-8").lower()
            for text in forbidden:
                with self.subTest(template=path.name, text=text):
                    self.assertNotIn(text, source)

    def test_css_desktop_sidebar_rule_is_not_duplicated(self):
        source = self.read("static/css/app.css")
        self.assertNotIn(".app-sidebar.offcanvas-xl {\n    .app-sidebar.offcanvas-xl {", source)
        self.assertIn(".responsive-definition-list", source)
        self.assertIn(".series-status-badge", source)

    def test_series_states_have_text_and_non_color_markers(self):
        for template in (
            "templates/lottery/series_list.html",
            "templates/lottery/series_detail.html",
        ):
            source = self.read(template)
            for marker in (
                "series-status--active",
                "series-status--paused",
                "series-status--completed",
                "series-status--archived",
            ):
                self.assertIn(marker, source)
            for label in ("Activa", "Pausada", "Completada", "Archivada"):
                self.assertIn(label, source)

    def test_all_tables_are_inside_responsive_regions(self):
        for path in (ROOT / "templates").rglob("*.html"):
            source = path.read_text(encoding="utf-8")
            if "<table" in source:
                with self.subTest(template=path.name):
                    self.assertIn("table-responsive", source)
