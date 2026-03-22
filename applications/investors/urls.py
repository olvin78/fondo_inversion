from django.urls import path
from . import views
from applications.investors.views import buy_participations_view, sell_participations_view

app_name = "investors"

urlpatterns = [
    path("", views.investor_list, name="investor_list"),
    path("create/", views.investor_create, name="investor_create"),
    path("invest/", views.invest, name="invest"),
    path("<int:pk>/", views.investor_detail, name="investor_detail"),
    path("buy/", buy_participations_view, name="buy_participations"),
    path("sell/", sell_participations_view, name="sell_participations"),

    # 👇 NOTIFICACIONES
    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/create/", views.notification_create, name="notification_create"),

    path(
        "notifications/create/monthly/",
        views.notification_create_monthly,
        name="notification_create_monthly",
    ),

    path(
        "notifications/create/informative/",
        views.notification_create_informative,  # 👈 AQUÍ
        name="notification_create_info",
    ),

    # 👇 SIEMPRE AL FINAL
    path(
        "notifications/<int:pk>/",
        views.notification_detail,
        name="notification_detail",
    ),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard-gestor/", views.dashboard_gestor, name="dashboard-gestor"),
    path("invest/", views.invest, name="invest"),
]
