from rest_framework.pagination import PageNumberPagination


class PublicApiPagination(PageNumberPagination):
    """
    Paginación estándar para colecciones públicas de API v1.

    El cliente puede solicitar un tamaño menor o mayor mediante
    ?page_size=, pero nunca superar max_page_size.
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100