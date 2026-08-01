"""Roles y metadatos de modo centralizados para evitar cadenas dispersas."""

CLIENT = "CLIENTE"
VENDOR = "VENDEDOR"
ADMINISTRATOR = "ADMINISTRADOR"

ROLE_CODES = (CLIENT, VENDOR, ADMINISTRATOR)

ROLE_PRESENTATION = {
    CLIENT: {
        "label": "Cliente",
        "title": "Modo Cliente",
        "description": "Consulta y operación de las funciones de cliente habilitadas.",
    },
    VENDOR: {
        "label": "Vendedor",
        "title": "Modo Vendedor",
        "description": "Atención de solicitudes y operaciones propias del vendedor.",
    },
    ADMINISTRATOR: {
        "label": "Administrador",
        "title": "Modo Administrador",
        "description": "Supervisión académica, catálogos e históricos protegidos.",
    },
}

DASHBOARD_URL_NAMES = {
    CLIENT: "core:client_dashboard",
    VENDOR: "core:vendor_dashboard",
    ADMINISTRATOR: "core:admin_dashboard",
}
