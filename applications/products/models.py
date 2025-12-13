from django.db import models

# Create your models here.
from django.db import models

class Product(models.Model):

    PRODUCT_TYPES = [
        ("STOCK", "Acciones"),
        ("ETF", "ETF"),
        ("FUND", "Fondo de inversión"),
        ("CRYPTO", "Criptomonedas"),
        ("COMMODITY", "Materias primas"),
        ("BOND", "Bonos"),
    ]

    REGION_CHOICES = [
        ("EU", "Europa"),
        ("NA", "Norteamérica"),
        ("SA", "Sudamérica"),
        ("ASIA", "Asia"),
        ("AF", "África"),
        ("OCE", "Oceanía"),
        ("GLOBAL", "Global"),
    ]

    COUNTRY_CHOICES = [
        ("AF", "Afganistán"),
        ("AL", "Albania"),
        ("DZ", "Argelia"),
        ("AS", "Samoa Americana"),
        ("AD", "Andorra"),
        ("AO", "Angola"),
        ("AI", "Anguila"),
        ("AQ", "Antártida"),
        ("AG", "Antigua y Barbuda"),
        ("AR", "Argentina"),
        ("AM", "Armenia"),
        ("AW", "Aruba"),
        ("AU", "Australia"),
        ("AT", "Austria"),
        ("AZ", "Azerbaiyán"),
        ("BS", "Bahamas"),
        ("BH", "Baréin"),
        ("BD", "Bangladés"),
        ("BB", "Barbados"),
        ("BY", "Bielorrusia"),
        ("BE", "Bélgica"),
        ("BZ", "Belice"),
        ("BJ", "Benín"),
        ("BM", "Bermudas"),
        ("BT", "Bután"),
        ("BO", "Bolivia"),
        ("BA", "Bosnia y Herzegovina"),
        ("BW", "Botsuana"),
        ("BR", "Brasil"),
        ("IO", "Territorio Británico del Océano Índico"),
        ("BN", "Brunéi"),
        ("BG", "Bulgaria"),
        ("BF", "Burkina Faso"),
        ("BI", "Burundi"),
        ("KH", "Camboya"),
        ("CM", "Camerún"),
        ("CA", "Canadá"),
        ("CV", "Cabo Verde"),
        ("KY", "Islas Caimán"),
        ("CF", "República Centroafricana"),
        ("TD", "Chad"),
        ("CL", "Chile"),
        ("CN", "China"),
        ("CO", "Colombia"),
        ("KM", "Comoras"),
        ("CG", "Congo"),
        ("CR", "Costa Rica"),
        ("HR", "Croacia"),
        ("CU", "Cuba"),
        ("CY", "Chipre"),
        ("CZ", "Chequia"),
        ("DK", "Dinamarca"),
        ("DJ", "Yibuti"),
        ("DO", "República Dominicana"),
        ("EC", "Ecuador"),
        ("EG", "Egipto"),
        ("SV", "El Salvador"),
        ("EE", "Estonia"),
        ("ET", "Etiopía"),
        ("FI", "Finlandia"),
        ("FR", "Francia"),
        ("GA", "Gabón"),
        ("GE", "Georgia"),
        ("DE", "Alemania"),
        ("GH", "Ghana"),
        ("GR", "Grecia"),
        ("GT", "Guatemala"),
        ("HN", "Honduras"),
        ("HK", "Hong Kong"),
        ("HU", "Hungría"),
        ("IS", "Islandia"),
        ("IN", "India"),
        ("ID", "Indonesia"),
        ("IR", "Irán"),
        ("IQ", "Irak"),
        ("IE", "Irlanda"),
        ("IL", "Israel"),
        ("IT", "Italia"),
        ("JM", "Jamaica"),
        ("JP", "Japón"),
        ("JO", "Jordania"),
        ("KZ", "Kazajistán"),
        ("KE", "Kenia"),
        ("KW", "Kuwait"),
        ("LV", "Letonia"),
        ("LB", "Líbano"),
        ("LY", "Libia"),
        ("LT", "Lituania"),
        ("LU", "Luxemburgo"),
        ("MY", "Malasia"),
        ("MX", "México"),
        ("MA", "Marruecos"),
        ("NL", "Países Bajos"),
        ("NZ", "Nueva Zelanda"),
        ("NG", "Nigeria"),
        ("NO", "Noruega"),
        ("PK", "Pakistán"),
        ("PA", "Panamá"),
        ("PE", "Perú"),
        ("PH", "Filipinas"),
        ("PL", "Polonia"),
        ("PT", "Portugal"),
        ("QA", "Catar"),
        ("RO", "Rumanía"),
        ("RU", "Rusia"),
        ("SA", "Arabia Saudí"),
        ("SG", "Singapur"),
        ("ZA", "Sudáfrica"),
        ("KR", "Corea del Sur"),
        ("ES", "España"),
        ("SE", "Suecia"),
        ("CH", "Suiza"),
        ("TH", "Tailandia"),
        ("TR", "Turquía"),
        ("UA", "Ucrania"),
        ("AE", "Emiratos Árabes Unidos"),
        ("GB", "Reino Unido"),
        ("US", "Estados Unidos"),
        ("UY", "Uruguay"),
        ("VE", "Venezuela"),
        ("VN", "Vietnam"),
        ("ZW", "Zimbabue"),
        ("GLOBAL", "Global"),
    ]

    SECTOR_CHOICES = [
        ("TECH", "Tecnología"),
        ("FIN", "Finanzas"),
        ("HEALTH", "Salud"),
        ("ENERGY", "Energía"),
        ("INDUSTRIAL", "Industrial"),
        ("CONSUMER", "Consumo"),
        ("UTILITIES", "Servicios públicos"),
        ("REAL_ESTATE", "Inmobiliario"),
        ("MATERIALS", "Materiales"),
    ]

    INDUSTRY_CHOICES = [
        ("SOFTWARE", "Software"),
        ("HARDWARE", "Hardware"),
        ("SEMICONDUCTORS", "Semiconductores"),
        ("BANKS", "Banca"),
        ("INSURANCE", "Seguros"),
        ("PHARMA", "Farmacéutica"),
        ("OIL_GAS", "Petróleo y gas"),
        ("RENEWABLES", "Energías renovables"),
        ("RETAIL", "Retail"),
    ]

    # Identificación
    name = models.CharField(max_length=100)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES)
    ticker = models.CharField(max_length=20, blank=True, null=True)
    isin = models.CharField(max_length=12, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Clasificación / diversificación
    region = models.CharField(max_length=10, choices=REGION_CHOICES, blank=True, null=True)
    country = models.CharField(max_length=10, choices=COUNTRY_CHOICES, blank=True, null=True)
    sector = models.CharField(max_length=20, choices=SECTOR_CHOICES, blank=True, null=True)
    industry = models.CharField(max_length=30, choices=INDUSTRY_CHOICES, blank=True, null=True)

    currency = models.CharField(max_length=10, default="EUR")

    # Datos opcionales de análisis
    dividend_yield = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    esg_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    # Control interno
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.product_type})"




class ProductPrice(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=12, decimal_places=4)
    date = models.DateTimeField()
