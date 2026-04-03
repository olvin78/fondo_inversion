from django.contrib import admin


class CustomAdminSite(admin.AdminSite):
    site_header = "Administración Fondo de Inversión"
    site_title = "Admin Fondo"
    index_title = "Gestión del sistema"

    def get_app_list(self, request):
        app_dict = self._build_app_dict(request)

        app_order = [
            "funds",        # Fondos y riesgo
            "investors",    # Inversores
            "portfolios",   # Carteras
            "transactions", # Transacciones
            "products",     # Productos
            "account",      # allauth
            "socialaccount",
            "auth",         # Usuarios y grupos
            "sites",        # Configuración técnica
        ]

        ordered_apps = []

        for app_label in app_order:
            if app_label in app_dict:
                ordered_apps.append(app_dict[app_label])

        # Añadir cualquier app no listada
        for app in app_dict.values():
            if app not in ordered_apps:
                ordered_apps.append(app)

        return ordered_apps


custom_admin_site = CustomAdminSite(name="custom_admin")
