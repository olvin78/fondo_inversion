def calculate_nav_from_ib(fund) -> Decimal:
    snapshot = IBSnapshot.objects.order_by("-created_at").first()
    if not snapshot:
        return Decimal("0")

    total = fund.total_participations()
    if total == 0:
        return Decimal("0")

    return snapshot.net_liquidation / total
