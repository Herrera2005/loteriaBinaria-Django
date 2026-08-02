from django.urls import path
from . import views
app_name = "lottery"
urlpatterns = [
    path("client/events/", views.ClientDrawEventListView.as_view(), name="client_event_list"),
    path("client/events/<int:pk>/", views.ClientDrawEventDetailView.as_view(), name="client_event_detail"),
    path("client/tickets/", views.ClientTicketListView.as_view(), name="client_ticket_list"),
    path("client/tickets/<int:pk>/", views.ClientTicketDetailView.as_view(), name="client_ticket_detail"),
    path("products/", views.LotteryProductListView.as_view(), name="product_list"),
    path("products/create/", views.LotteryProductCreateView.as_view(), name="product_create"),
    path("products/<int:pk>/", views.LotteryProductDetailView.as_view(), name="product_detail"),
    path("products/<int:pk>/edit/", views.LotteryProductUpdateView.as_view(), name="product_update"),
    path("products/<int:pk>/delete/", views.LotteryProductDeleteView.as_view(), name="product_delete"),
    path("events/", views.DrawEventListView.as_view(), name="event_list"),
    path("events/create/", views.DrawEventCreateView.as_view(), name="event_create"),
    path("events/<int:pk>/", views.DrawEventDetailView.as_view(), name="event_detail"),
    path("events/<int:pk>/edit/", views.DrawEventUpdateView.as_view(), name="event_update"),
    path("events/<int:pk>/transition/<str:to_status>/", views.DrawEventTransitionView.as_view(), name="event_transition"),
    path("events/<int:pk>/publish-result/", views.DrawResultPublishView.as_view(), name="result_publish"),
    path("results/<int:pk>/", views.PublicDrawResultDetailView.as_view(), name="public_result_detail"),
    path("events/<int:pk>/delete/", views.DrawEventDeleteView.as_view(), name="event_delete"),
]
