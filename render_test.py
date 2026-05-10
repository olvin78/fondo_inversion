import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.template.loader import render_to_string
from applications.funds.models import Fund
import datetime
from django.utils import timezone

fund = Fund.objects.get(id=1)
valores = fund.valores_diarios.all().order_by("fecha")
diversification = fund.diversification.all()

context = {
    'fund': fund,
    'valores_diarios': valores,
    'diversification': diversification,
    'range_start': '2026-04-10',
    'range_end': '2026-05-10',
}

rendered = render_to_string('funds/fund_detail.html', context)

# Extraer el bloque de javascript para analizar
import re
js_block = re.search(r'<script>(.*?)</script>', rendered, re.DOTALL)
if js_block:
    js = js_block.group(1)
    for line in js.split('\n'):
        if 'const navData' in line or 'const navLabels' in line or 'const divValues' in line:
            print(line.strip())
