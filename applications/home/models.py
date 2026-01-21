from django.db import models
from applications.products.models import Country
from django.contrib.gis.db import models as gis_models

class MapElementType(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True,
        help_text="Código interno (ej: MARKET, CENTRAL_BANK)",
        blank = True,
        null = True,
    )

    name = models.CharField(
        max_length=100,
        help_text="Nombre visible"
    )

    icon = models.ImageField(
        upload_to="map_icons/",
        blank=True,
        null=True,
        help_text="Icono para el mapa (PNG / SVG recomendado)"
    )

    description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Map element type"
        verbose_name_plural = "Map element types"
        ordering = ("name",)

    def __str__(self):
        return self.name


class MapElement(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        help_text="Código interno o abreviatura (opcional)"
    )

    name = models.CharField(
        max_length=150,
        help_text="Nombre visible"
    )

    element_type = models.ForeignKey(
        MapElementType,
        on_delete=models.PROTECT,
        related_name="elements"
    )

    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="map_elements"
    )

    description = models.TextField(blank=True)

    location = gis_models.PointField(
        geography=True,
        srid=4326,
        help_text="Ubicación geográfica (lon, lat)"
    )

    is_active = models.BooleanField(default=True)
    show_in_map = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
