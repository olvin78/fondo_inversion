FROM python:3.11-slim

# ===============================
# Dependencias del sistema (GeoDjango)
# ===============================
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libproj-dev \
    libgeos-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Variables de entorno necesarias para GeoDjango
ENV GDAL_LIBRARY_PATH=/usr/lib/libgdal.so
ENV GEOS_LIBRARY_PATH=/usr/lib/libgeos_c.so

# ===============================
# App
# ===============================
WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
