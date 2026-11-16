from django.urls import path

from alerts import views


urlpatterns = [
    path("", views.root, name="root"),
    path("alerts/", views.alert_collection, name="alert-list-create"),
    path("alerts/<int:alert_id>", views.alert_detail, name="alert-detail"),
    path(
        "alerts/<int:alert_id>/explain",
        views.explain_alert,
        name="alert-explain",
    ),
]