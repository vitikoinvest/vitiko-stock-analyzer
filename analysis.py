"""Indicadores calculados exclusivamente a partir de cierres disponibles."""
import numpy as np
import pandas as pd


def indicators(prices: pd.DataFrame) -> pd.DataFrame:
    data = prices.copy()
    close = data['Close']
    for window in (50, 100, 200):
        data[f'SMA{window}'] = close.rolling(window, min_periods=window).mean()
    delta = close.diff()
    # Suavizado de Wilder: semilla = media de las primeras 14 variaciones.
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)
    def wilder(series):
        result = pd.Series(np.nan, index=series.index)
        if len(series) > 14:
            result.iloc[14] = series.iloc[1:15].mean()
            for i in range(15, len(series)):
                result.iloc[i] = (result.iloc[i-1] * 13 + series.iloc[i]) / 14
        return result
    gain, loss = wilder(gains), wilder(losses)
    data['RSI'] = 100 - 100 / (1 + gain / loss)
    data.loc[(loss == 0) & (gain > 0), 'RSI'] = 100
    data.loc[(loss == 0) & (gain == 0), 'RSI'] = 50
    fast = close.ewm(span=12, adjust=False, min_periods=12).mean()
    slow = close.ewm(span=26, adjust=False, min_periods=26).mean()
    data['MACD'] = fast - slow
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False, min_periods=9).mean()
    data['Histogram'] = data['MACD'] - data['Signal']
    return data


def trend(data):
    last = data.iloc[-1]
    if pd.isna(last['SMA200']) or len(data) < 221:
        return 'Datos insuficientes', 'Se necesitan al menos 221 sesiones para comparar el precio, las medias y su evolución.'
    slope = last['SMA200'] / data['SMA200'].iloc[-21] - 1
    if last['Close'] > last['SMA50'] > last['SMA200'] and slope > .005:
        return 'Alcista', 'El precio supera las medias de 50 y 200 sesiones y la media de largo plazo está subiendo.'
    if last['Close'] < last['SMA50'] < last['SMA200'] and slope < -.005:
        return 'Bajista', 'El precio está por debajo de las medias de 50 y 200 sesiones y la media de largo plazo está bajando.'
    return 'Lateral / señales mixtas', 'Las medias y el precio no muestran una dirección consistente. Esta regla orientativa no predice el futuro.'


def levels(data):
    recent = data.tail(60)
    return float(recent['Close'].min()), float(recent['Close'].max())
