from decimal import Decimal


def roi(net: Decimal | None, required: Decimal | None) -> Decimal | None:
    return net / required if net is not None and required is not None and required > 0 else None


def annualized(net: Decimal, required: Decimal, days: Decimal | None) -> Decimal | None:
    return net / required * Decimal(365) / days if required > 0 and days and days > 0 else None
