from django.urls import path

from . import views

app_name = "api"

urlpatterns = [
    path("", views.api_root, name="root"),
    path("products/", views.product_list, name="product_list"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("events/", views.event_list, name="event_list"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("results/", views.result_list, name="result_list"),
    path("results/<int:pk>/", views.result_detail, name="result_detail"),
]
