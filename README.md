# Binance Futures Testnet Trading Bot

A clean, production-structured Python CLI application for placing orders on the **Binance Futures Testnet (USDT-M)**.

---

## Features

| Feature | Detail |
|---|---|
| Order types | MARKET, LIMIT, STOP\_MARKET (bonus) |
| Sides | BUY & SELL |
| CLI | `argparse` with validation, clear error messages |
| Logging | Structured file + console logging (`logs/trading_bot_YYYYMMDD.log`) |
| Error handling | Input validation, API errors, network failures all caught and reported clearly |
| Structure | Separate client / orders / validators / CLI layers |

---

## Project Structure

```
trading_bot/
├── bot/
│   ├── __init__.py
│   ├── client.py          # Binance REST client (signing, requests, error handling)
│   ├── orders.py          # Order placement logic (MARKET, LIMIT, STOP_MARKET)
│   ├── validators.py      # Input validation
│   └── logging_config.py  # Structured logging setup
├── logs/                  # Auto-created; log files written here
├── cli.py                 # CLI entry point
├── .env.example           # Credentials template
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Setup

### 1. Get Testnet API Credentials

1. Go to [https://testnet.binancefuture.com](https://testnet.binancefuture.com)
2. Log in with your GitHub account
3. Click **API Key** tab → copy your key and secret

### 2. Clone & install dependencies

```bash
git clone <your-repo-url>
cd trading_bot

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure credentials

```bash
cp .env.example .env
# Edit .env and paste your API key and secret
```

`.env` contents:
```
BINANCE_API_KEY=your_testnet_api_key_here
BINANCE_API_SECRET=your_testnet_api_secret_here
```

> **Never commit `.env` to Git.** It is already in `.gitignore`.

---

## Usage

### MARKET Order

```bash
python cli.py --symbol BTCUSDT --side BUY --type MARKET --qty 0.001
```

### LIMIT Order

```bash
python cli.py --symbol BTCUSDT --side SELL --type LIMIT --qty 0.001 --price 50000
```

### STOP\_MARKET Order (bonus order type)

```bash
python cli.py --symbol BTCUSDT --side SELL --type STOP_MARKET --qty 0.001 --stop-price 40000
```

### All CLI flags

| Flag | Required | Description |
|---|---|---|
| `--symbol` | ✅ | Trading pair, e.g. `BTCUSDT` |
| `--side` | ✅ | `BUY` or `SELL` |
| `--type` | ✅ | `MARKET`, `LIMIT`, or `STOP_MARKET` |
| `--qty` | ✅ | Order quantity (e.g. `0.001`) |
| `--price` | LIMIT only | Limit price |
| `--stop-price` | STOP\_MARKET only | Stop trigger price |
| `--tif` | No | Time-in-force for LIMIT (default: `GTC`) |
| `--log-level` | No | `DEBUG`, `INFO`, `WARNING` (default: `INFO`) |

---

## Example Output

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Binance Futures Testnet Trading Bot
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋  Order Summary
  Symbol    : BTCUSDT
  Side      : BUY
  Type      : MARKET
  Quantity  : 0.001

✅  Order Placed Successfully!

📄  Order Details
  Order ID        : 3942611
  Status          : FILLED
  Symbol          : BTCUSDT
  Side            : BUY
  Type            : MARKET
  Orig Qty        : 0.001
  Executed Qty    : 0.001
  Avg Price       : 67543.20
```

---

## Log Files

Logs are written to `logs/trading_bot_YYYYMMDD.log`. Each entry contains timestamp, level, module, and message.

Sample log output:

```
2025-01-15 14:23:01 | INFO     | trading_bot.client | REQUEST  POST /fapi/v1/order | params={'symbol': 'BTCUSDT', 'side': 'BUY', 'type': 'MARKET', 'quantity': 0.001}
2025-01-15 14:23:02 | INFO     | trading_bot.client | RESPONSE 200 | {"orderId":3942611,"symbol":"BTCUSDT",...}
2025-01-15 14:23:02 | INFO     | trading_bot.orders | MARKET order placed successfully | orderId=3942611 status=FILLED
```

---

## Error Handling

The bot handles these failure modes gracefully:

| Error | Behaviour |
|---|---|
| Invalid symbol/side/type | Validation error shown before any API call |
| Missing price for LIMIT | Clear validation error |
| Wrong API credentials | API error code shown |
| Network timeout/failure | Clear network error message |
| Binance API error (e.g. insufficient balance) | Error code + message shown |

---

## Assumptions

- **Testnet only**: This bot targets `https://testnet.binancefuture.com`. Do not use production keys.
- **USDT-M futures**: All orders are placed on USD-margined perpetual contracts.
- **Minimum quantity**: Binance testnet enforces minimum notional values. For BTC use `0.001` or higher.
- **No position management**: This bot only places orders. It does not manage open positions or track P&L.
- **Credentials via `.env`**: The bot reads `BINANCE_API_KEY` and `BINANCE_API_SECRET` from environment variables or a `.env` file.

---

## Tech Stack

- Python 3.10+
- `requests` – HTTP client for REST API calls
- `python-dotenv` – Environment variable loading
- Standard library: `argparse`, `logging`, `hmac`, `hashlib`
