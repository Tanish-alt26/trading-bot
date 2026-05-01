"""
validators.py – input validation for CLI arguments.
All validators raise ValueError with a human-readable message on failure.
"""

VALID_SIDES = {"BUY", "SELL"}
VALID_ORDER_TYPES = {"MARKET", "LIMIT", "STOP_MARKET"}


def validate_symbol(symbol: str) -> str:
    """Ensure the symbol is a non-empty uppercase string like BTCUSDT."""
    symbol = symbol.strip().upper()
    if not symbol.isalnum():
        raise ValueError(
            f"Invalid symbol '{symbol}'. Must be alphanumeric, e.g. BTCUSDT."
        )
    return symbol


def validate_side(side: str) -> str:
    """Ensure side is BUY or SELL."""
    side = side.strip().upper()
    if side not in VALID_SIDES:
        raise ValueError(
            f"Invalid side '{side}'. Must be one of: {', '.join(sorted(VALID_SIDES))}."
        )
    return side


def validate_order_type(order_type: str) -> str:
    """Ensure order type is supported."""
    order_type = order_type.strip().upper()
    if order_type not in VALID_ORDER_TYPES:
        raise ValueError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(sorted(VALID_ORDER_TYPES))}."
        )
    return order_type


def validate_quantity(quantity: str) -> float:
    """Ensure quantity is a positive number."""
    try:
        qty = float(quantity)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid quantity '{quantity}'. Must be a positive number.")
    if qty <= 0:
        raise ValueError(f"Quantity must be greater than 0, got {qty}.")
    return qty


def validate_price(price: str | None, order_type: str) -> float | None:
    """
    Price is required for LIMIT and STOP_MARKET orders.
    Returns None for MARKET orders.
    """
    if order_type == "MARKET":
        return None

    if price is None:
        raise ValueError(f"Price is required for {order_type} orders.")

    try:
        p = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid price '{price}'. Must be a positive number.")

    if p <= 0:
        raise ValueError(f"Price must be greater than 0, got {p}.")

    return p


def validate_stop_price(stop_price: str | None, order_type: str) -> float | None:
    """Stop price is required for STOP_MARKET orders."""
    if order_type != "STOP_MARKET":
        return None

    if stop_price is None:
        raise ValueError("Stop price (--stop-price) is required for STOP_MARKET orders.")

    try:
        sp = float(stop_price)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid stop price '{stop_price}'. Must be a positive number.")

    if sp <= 0:
        raise ValueError(f"Stop price must be greater than 0, got {sp}.")

    return sp
