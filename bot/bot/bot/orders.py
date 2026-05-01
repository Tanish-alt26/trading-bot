"""
orders.py – order placement logic, sitting between the CLI and the raw client.

Builds the correct parameter payload for each order type, calls the client,
and returns a normalised result dict for display.
"""

import logging
from typing import Any

from .client import BinanceClient, BinanceAPIError

logger = logging.getLogger("trading_bot.orders")


def _normalise_response(raw: dict) -> dict:
    """Extract the fields we care about into a clean dict."""
    return {
        "orderId": raw.get("orderId"),
        "symbol": raw.get("symbol"),
        "side": raw.get("side"),
        "type": raw.get("type"),
        "origQty": raw.get("origQty"),
        "executedQty": raw.get("executedQty"),
        "avgPrice": raw.get("avgPrice"),
        "price": raw.get("price"),
        "stopPrice": raw.get("stopPrice"),
        "status": raw.get("status"),
        "timeInForce": raw.get("timeInForce"),
        "clientOrderId": raw.get("clientOrderId"),
        "updateTime": raw.get("updateTime"),
    }


def place_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
) -> dict[str, Any]:
    """Place a MARKET order."""
    params = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": quantity,
    }
    logger.info(f"Placing MARKET order | symbol={symbol} side={side} qty={quantity}")
    raw = client.place_order(params)
    result = _normalise_response(raw)
    logger.info(f"MARKET order placed successfully | orderId={result['orderId']} status={result['status']}")
    return result


def place_limit_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    price: float,
    time_in_force: str = "GTC",
) -> dict[str, Any]:
    """Place a LIMIT order."""
    params = {
        "symbol": symbol,
        "side": side,
        "type": "LIMIT",
        "quantity": quantity,
        "price": price,
        "timeInForce": time_in_force,
    }
    logger.info(
        f"Placing LIMIT order | symbol={symbol} side={side} qty={quantity} price={price} tif={time_in_force}"
    )
    raw = client.place_order(params)
    result = _normalise_response(raw)
    logger.info(f"LIMIT order placed successfully | orderId={result['orderId']} status={result['status']}")
    return result


def place_stop_market_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    quantity: float,
    stop_price: float,
) -> dict[str, Any]:
    """Place a STOP_MARKET order (bonus order type)."""
    params = {
        "symbol": symbol,
        "side": side,
        "type": "STOP_MARKET",
        "quantity": quantity,
        "stopPrice": stop_price,
        "closePosition": "false",
    }
    logger.info(
        f"Placing STOP_MARKET order | symbol={symbol} side={side} qty={quantity} stopPrice={stop_price}"
    )
    raw = client.place_order(params)
    result = _normalise_response(raw)
    logger.info(f"STOP_MARKET order placed successfully | orderId={result['orderId']} status={result['status']}")
    return result


def dispatch_order(
    client: BinanceClient,
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None = None,
    stop_price: float | None = None,
    time_in_force: str = "GTC",
) -> dict[str, Any]:
    """
    Route to the correct placement function based on order_type.
    Raises ValueError for unknown types, BinanceAPIError on API failures.
    """
    if order_type == "MARKET":
        return place_market_order(client, symbol, side, quantity)
    elif order_type == "LIMIT":
        if price is None:
            raise ValueError("Price is required for LIMIT orders.")
        return place_limit_order(client, symbol, side, quantity, price, time_in_force)
    elif order_type == "STOP_MARKET":
        if stop_price is None:
            raise ValueError("Stop price is required for STOP_MARKET orders.")
        return place_stop_market_order(client, symbol, side, quantity, stop_price)
    else:
        raise ValueError(f"Unsupported order type: '{order_type}'.")
