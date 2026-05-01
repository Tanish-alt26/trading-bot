#!/usr/bin/env python3
"""
cli.py – Command-line entry point for the Binance Futures Testnet Trading Bot.

Usage examples:
  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --qty 0.001
  python cli.py --symbol BTCUSDT --side SELL --type LIMIT  --qty 0.001 --price 50000
  python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.001 --stop-price 40000
"""

import argparse
import os
import sys
from dotenv import load_dotenv

from bot.logging_config import setup_logging
from bot.client import BinanceClient, BinanceAPIError
from bot.orders import dispatch_order
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)

# ── ANSI colour helpers (degrade gracefully on Windows) ──────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"


def _c(text: str, colour: str) -> str:
    """Apply colour only when stdout is a TTY."""
    if sys.stdout.isatty():
        return f"{colour}{text}{RESET}"
    return text


def print_banner():
    print(_c("━" * 55, CYAN))
    print(_c("   Binance Futures Testnet Trading Bot", BOLD))
    print(_c("━" * 55, CYAN))


def print_order_summary(args: argparse.Namespace):
    """Print what we are about to send."""
    print()
    print(_c("📋  Order Summary", BOLD))
    print(f"  Symbol    : {_c(args.symbol, CYAN)}")
    print(f"  Side      : {_c(args.side, GREEN if args.side == 'BUY' else RED)}")
    print(f"  Type      : {args.type}")
    print(f"  Quantity  : {args.qty}")
    if args.price:
        print(f"  Price     : {args.price}")
    if args.stop_price:
        print(f"  Stop Price: {args.stop_price}")
    print()


def print_order_result(result: dict):
    """Pretty-print the normalised order response."""
    print(_c("✅  Order Placed Successfully!", GREEN))
    print()
    print(_c("📄  Order Details", BOLD))
    fields = [
        ("Order ID",     "orderId"),
        ("Status",       "status"),
        ("Symbol",       "symbol"),
        ("Side",         "side"),
        ("Type",         "type"),
        ("Orig Qty",     "origQty"),
        ("Executed Qty", "executedQty"),
        ("Avg Price",    "avgPrice"),
        ("Limit Price",  "price"),
        ("Stop Price",   "stopPrice"),
        ("Time-In-Force","timeInForce"),
        ("Client OID",   "clientOrderId"),
    ]
    for label, key in fields:
        val = result.get(key)
        if val not in (None, "", "0", "0.00000000", "0.000"):
            print(f"  {label:<16}: {val}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trading_bot",
        description="Place orders on Binance Futures Testnet (USDT-M)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --symbol BTCUSDT --side BUY  --type MARKET --qty 0.001
  python cli.py --symbol ETHUSDT --side SELL --type LIMIT  --qty 0.01 --price 1800
  python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.001 --stop-price 40000
        """,
    )
    parser.add_argument("--symbol",     required=True,  help="Trading pair, e.g. BTCUSDT")
    parser.add_argument("--side",       required=True,  help="BUY or SELL")
    parser.add_argument("--type",       required=True,  help="MARKET, LIMIT, or STOP_MARKET")
    parser.add_argument("--qty",        required=True,  help="Order quantity")
    parser.add_argument("--price",      default=None,   help="Limit price (required for LIMIT orders)")
    parser.add_argument("--stop-price", default=None,   dest="stop_price",
                        help="Stop trigger price (required for STOP_MARKET orders)")
    parser.add_argument("--tif",        default="GTC",  help="Time-in-force for LIMIT orders (default: GTC)")
    parser.add_argument("--log-level",  default="INFO", help="Logging level (default: INFO)")
    return parser


def main():
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    logger = setup_logging(args.log_level)
    print_banner()

    # ── Validate inputs ──────────────────────────────────────────────────────
    try:
        args.symbol     = validate_symbol(args.symbol)
        args.side       = validate_side(args.side)
        args.type       = validate_order_type(args.type)
        args.qty        = validate_quantity(args.qty)
        args.price      = validate_price(args.price, args.type)
        args.stop_price = validate_stop_price(args.stop_price, args.type)
    except ValueError as exc:
        print(_c(f"\n❌  Validation Error: {exc}\n", RED))
        logger.error(f"Validation failed: {exc}")
        sys.exit(1)

    # ── Load API credentials ─────────────────────────────────────────────────
    api_key    = os.getenv("BINANCE_API_KEY", "").strip()
    api_secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not api_key or not api_secret:
        msg = (
            "BINANCE_API_KEY and BINANCE_API_SECRET must be set.\n"
            "  Copy .env.example → .env and add your Testnet credentials."
        )
        print(_c(f"\n❌  {msg}\n", RED))
        logger.error("Missing API credentials.")
        sys.exit(1)

    # ── Initialise client & place order ──────────────────────────────────────
    client = BinanceClient(api_key=api_key, api_secret=api_secret)

    print_order_summary(args)

    try:
        result = dispatch_order(
            client=client,
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=args.qty,
            price=args.price,
            stop_price=args.stop_price,
            time_in_force=args.tif,
        )
        print_order_result(result)

    except BinanceAPIError as exc:
        print(_c(f"\n❌  Binance API Error [{exc.code}]: {exc.message}\n", RED))
        logger.error(f"API error: code={exc.code} msg={exc.message}")
        sys.exit(1)

    except (ConnectionError, TimeoutError) as exc:
        print(_c(f"\n❌  Network Error: {exc}\n", RED))
        logger.error(f"Network error: {exc}")
        sys.exit(1)

    except Exception as exc:
        print(_c(f"\n❌  Unexpected error: {exc}\n", RED))
        logger.exception("Unexpected error during order placement.")
        sys.exit(1)


if __name__ == "__main__":
    main()
