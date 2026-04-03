from decimal import Decimal

from applications.ib.models import IBSnapshot
from core.utils.decimal import round4


def calculate_nav_from_ib(fund) -> Decimal:
    snapshot = IBSnapshot.objects.order_by("-created_at").first()
    if not snapshot:
        return Decimal("0.0000")

    total = fund.total_participations()
    if total == 0:
        return Decimal("0.0000")

    return round4(snapshot.net_liquidation / total)
