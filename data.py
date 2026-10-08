"""Fuente real: Yahoo Finance mediante yfinance. La demo nunca sustituye errores."""
import re
import numpy as np
import pandas as pd
import yfinance as yf


def validate_ticker(ticker):
    ticker = ticker.strip().upper()
    if not re.fullmatch(r'[A-Z]{1,6}(?:[.-][A-Z]{1,2})?', ticker):
        raise ValueError('Introduce un ticker válido, por ejemplo AMZN, MSFT o BRK-B.')
    return ticker


def load_prices(ticker):
    ticker = validate_ticker(ticker)
    prices = yf.Ticker(ticker).history(period='5y', interval='1d', auto_adjust=True, raise_errors=True)
    if prices.empty or 'Close' not in prices:
        raise ValueError('La fuente no devolvió precios. Comprueba el ticker o inténtalo más tarde.')
    close = pd.to_numeric(prices['Close'], errors='coerce')
    prices = prices.loc[close.notna() & np.isfinite(close) & (close > 0), ['Close']].copy()
    prices = prices.sort_index()
    prices = prices.loc[~prices.index.duplicated(keep='last')]
    if prices.empty:
        raise ValueError('No hay cierres válidos disponibles.')
    return prices


def demo_prices():
    rng = np.random.default_rng(42)
    dates = pd.bdate_range('2022-01-03', '2025-12-31')
    close = 100 * np.exp(np.cumsum(rng.normal(.0003, .012, len(dates))))
    return pd.DataFrame({'Close': close}, index=dates)
