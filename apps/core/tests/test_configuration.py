import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import SimpleTestCase
from django.urls import reverse


class ConfigurationTests(SimpleTestCase):
    def test_phase_one_uses_sqlite(self):
        self.assertEqual(
            settings.DATABASES["default"]["ENGINE"],
            "django.db.backends.sqlite3",
        )

    def test_relative_sqlite_url_resolves_under_project_root(self):
        database_name = Path(settings.DATABASES["default"]["NAME"])
        self.assertTrue(database_name.is_absolute())
        self.assertEqual(database_name.parent, Path(settings.BASE_DIR))


    def test_postgresql_database_url_is_rejected_for_this_workshop(self):
        environment = os.environ.copy()
        environment.update(
            {
                "DATABASE_URL": "postgresql://user:password@127.0.0.1:5432/forbidden",
                "DJANGO_DEBUG": "True",
            }
        )
        result = subprocess.run(
            [sys.executable, "manage.py", "check"],
            cwd=settings.BASE_DIR,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

        combined_output = f"{result.stdout}\n{result.stderr}"
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("únicamente SQLite en fase 1 y MySQL en fase 2", combined_output)

    def test_expected_routes_reverse(self):
        expected = {
            "core:home": "/",
            "accounts:login": "/accounts/login/",
            "accounts:logout": "/accounts/logout/",
            "accounts:register": "/accounts/register/",
            "accounts:choose_mode": "/accounts/mode/",
            "core:client_dashboard": "/dashboard/client/",
            "core:vendor_dashboard": "/dashboard/vendor/",
            "core:admin_dashboard": "/dashboard/admin/",
        }
        for name, path in expected.items():
            with self.subTest(name=name):
                self.assertEqual(reverse(name), path)

    def test_required_static_files_are_discoverable(self):
        for relative_path in (
            "css/app.css",
            "js/app.js",
            "img/logo-placeholder.png",
        ):
            with self.subTest(relative_path=relative_path):
                self.assertIsNotNone(finders.find(relative_path))

    def test_backup_zip_is_preserved_but_outside_runtime_static(self):
        backup = Path(settings.BASE_DIR) / "respaldo_frontend" / (
            "Proyecto_HerreraNietoCristhian_legacy.zip"
        )
        self.assertTrue(backup.is_file())
        self.assertNotIn("respaldo_frontend", settings.STATICFILES_DIRS)
