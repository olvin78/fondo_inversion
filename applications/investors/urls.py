from django.urls import path
from . import views
from applications.investors.views import buy_participations_view, sell_participations_view

app_name = "investors"

urlpatterns = [
    path("", views.investor_list, name="investor_list"),
    path("create/", views.investor_create, name="investor_create"),
    path("invest/", views.invest, name="invest"),
    path("<int:pk>/", views.investor_detail, name="investor_detail"),
    path("<int:pk>/evolution-data/", views.investor_evolution_data, name="investor_evolution_data"),
    path("buy/", buy_participations_view, name="buy_participations"),
    path("sell/", sell_participations_view, name="sell_participations"),

    # 👇 NOTIFICACIONES
    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/create/", views.notification_create, name="notification_create"),
    path("notifications/send/", views.notification_send, name="notification_send"),

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
    path(
        "notifications/create/buy/",
        views.notification_create_buy,
        name="notification_create_buy",
    ),
    path(
        "notifications/create/sell/",
        views.notification_create_sell,
        name="notification_create_sell",
    ),

    # 👇 SIEMPRE AL FINAL
    path(
        "notifications/<int:pk>/",
        views.notification_detail,
        name="notification_detail",
    ),

    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard-gestor/", views.dashboard_gestor, name="dashboard-gestor"),
    path("transactions/", views.transaction_list_full, name="transaction_list_full"),
    path("invest/", views.invest, name="invest"),
    path("convert-honorarios/", views.convert_honorarios_view, name="convert_honorarios"),
]
