from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models as gis_models





class Currency(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    symbol = models.CharField(max_length=5, blank=True)

    def __str__(self):
        return self.code


class Strategy(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Sector(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Industry(models.Model):
    sector = models.ForeignKey(Sector, on_delete=models.CASCADE, related_name="industries")
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("sector", "code")

    def __str__(self):
        return f"{self.sector.name} - {self.name}"



class Region(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class MarketType(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Country(models.Model):
    iso_code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True)
    currency = models.CharField(max_length=10)
    risk_rating = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name





class AssetClass(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=150)

    asset_class = models.ForeignKey(
        AssetClass, on_delete=models.PROTECT, related_name="products"
    )

    ticker = models.CharField(max_length=30, blank=True, null=True)
    isin = models.CharField(max_length=12, blank=True, null=True)

    country = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True
    )

    sector = models.ForeignKey(
        Sector, on_delete=models.SET_NULL, null=True, blank=True
    )

    industry = models.ForeignKey(
        Industry, on_delete=models.SET_NULL, null=True, blank=True
    )

    strategy = models.ForeignKey(
        Strategy, on_delete=models.SET_NULL, null=True, blank=True
    )

    currency = models.ForeignKey(
        Currency, on_delete=models.PROTECT
    )

    dividend_yield = models.DecimalField(
        max_digits=6, decimal_places=3, null=True, blank=True
    )

    esg_score = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )

    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    location = gis_models.PointField(
        srid=4326,
        blank=True,
        null=True,
        help_text="Ubicación geográfica del activo (lat/lng)"
    )
    show_in_map = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.country is None and self.location:
            raise ValidationError(
                "Un producto sin país no debe tener localización geográfica."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class ProductPrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    date = models.DateTimeField()
