#!/bin/bash
# Despliegue automático fondo_inversion
echo "🚀 Iniciando despliegue de fondo_inversion..."
cd /var/www/fondo_inversion || exit
git pull origin main
source env/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart fondocapital
sudo systemctl status fondocapital
echo "✅ Despliegue completado con éxito."
