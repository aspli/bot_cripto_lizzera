# Crypto Trading Bot

A professional algorithmic trading bot for cryptocurrencies built with Python, CCXT, Pandas, and SQLAlchemy.

## Features

- **Data Collection**: OHLCV data via CCXT for multiple pairs and timeframes.
- **Strategy**: Trend Following (EMA20/50, RSI, EMA200 trend filter).
- **Risk Management**: 1% risk per trade, configurable SL/TP.
- **Execution**: Paper Trading mode with database persistence.
- **Backtesting**: Integration with `backtesting.py`.
- **Notifications**: Telegram alerts.
- **Database**: PostgreSQL integration.
- **Deployment**: Docker and docker-compose ready.

## Quick Start

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in your credentials.
3. Start via Docker:
   ```bash
   docker-compose up -d --build
   ```

## Development & Testing

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run unit tests:
   ```bash
   pytest tests/
   ```
3. Run Backtest:
   ```bash
   python backtest.py
   ```

## Architecture Overview
- `app/config/`: Configuration loaded from `.env`.
- `app/data/`: Data gathering via CCXT and SQLAlchemy models.
- `app/strategies/`: Trading strategies.
- `app/risk_management/`: Position sizing and checks.
- `app/execution/`: Handlers for paper and live trading.
- `app/notifications/`: Telegram bot alerts.
