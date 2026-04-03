from decimal import Decimal, ROUND_HALF_UP

DECIMAL_4 = Decimal("0.0001")


def round4(value) -> Decimal:
    if value is None:
        return Decimal("0.0000")
    return Decimal(value).quantize(DECIMAL_4, rounding=ROUND_HALF_UP)


def quantize_4(value: Decimal) -> Decimal:
    return round4(value)
