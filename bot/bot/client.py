"""
client.py – low-level Binance Futures Testnet REST client.

Handles:
  - HMAC-SHA256 request signing
  - Timestamping
  - Logging of every request/response
  - Structured exception handling
"""

import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import urlencode

import requests

logger = logging.getLogger("trading_bot.client")

BASE_URL = "https://testnet.binancefuture.com"


class BinanceAPIError(Exception):
    """Raised when the Binance API returns an error response."""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"Binance API Error {code}: {message}")


class BinanceClient:
    """Thin wrapper around Binance Futures Testnet REST API."""

    def __init__(self, api_key: str, api_secret: str, base_url: str = BASE_URL):
        if not api_key or not api_secret:
            raise ValueError("API key and secret must not be empty.")
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-MBX-APIKEY": self.api_key,
                "Content-Type": "application/x-www-form-urlencoded",
            }
        )
        logger.info(f"BinanceClient initialised — base URL: {self.base_url}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sign(self, params: dict) -> dict:
        """Append a signature to the parameter dict (mutates and returns it)."""
        params["timestamp"] = int(time.time() * 1000)
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        signed: bool = False,
    ) -> Any:
        """Send an HTTP request, log it, and return parsed JSON."""
        params = params or {}
        if signed:
            params = self._sign(params)

        url = f"{self.base_url}{path}"
        # Log before sending (exclude signature for brevity)
        log_params = {k: v for k, v in params.items() if k != "signature"}
        logger.info(f"REQUEST  {method.upper()} {path} | params={log_params}")

        try:
            if method.upper() in ("GET", "DELETE"):
                response = self.session.request(method, url, params=params, timeout=10)
            else:
                response = self.session.request(method, url, data=params, timeout=10)
        except requests.exceptions.ConnectionError as exc:
            logger.error(f"Network error connecting to {url}: {exc}")
            raise ConnectionError(f"Cannot reach Binance Testnet ({self.base_url}). Check your internet connection.") from exc
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out: {method} {url}")
            raise TimeoutError("Binance API request timed out after 10 seconds.")

        logger.info(f"RESPONSE {response.status_code} | {response.text[:500]}")

        try:
            data = response.json()
        except ValueError:
            logger.error(f"Non-JSON response: {response.text[:200]}")
            raise BinanceAPIError(-1, f"Unexpected non-JSON response: {response.text[:200]}")

        if isinstance(data, dict) and "code" in data and data["code"] < 0:
            raise BinanceAPIError(data["code"], data.get("msg", "Unknown error"))

        return data

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------

    def get_server_time(self) -> dict:
        """Ping the server to verify connectivity."""
        return self._request("GET", "/fapi/v1/time")

    def get_exchange_info(self, symbol: str) -> dict:
        """Fetch symbol metadata (filters, tick size, etc.)."""
        return self._request("GET", "/fapi/v1/exchangeInfo", params={"symbol": symbol})

    def place_order(self, params: dict) -> dict:
        """Submit a new order to Binance Futures."""
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def get_order(self, symbol: str, order_id: int) -> dict:
        """Query an existing order by ID."""
        return self._request(
            "GET",
            "/fapi/v1/order",
            params={"symbol": symbol, "orderId": order_id},
            signed=True,
        )

    def get_account(self) -> dict:
        """Fetch account information including balance."""
        return self._request("GET", "/fapi/v2/account", params={}, signed=True)
