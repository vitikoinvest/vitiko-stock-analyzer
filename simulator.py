"""Trayectorias deterministas educativas; nunca predicciones ni operaciones."""
import numpy as np
import pandas as pd
from analysis import indicators
from position import validate_shares


def simulate(history, initial, change, months, shape='Lineal', oscillation=0.):
    if months not in (1, 3, 6, 12):
        raise ValueError('Horizonte no válido.')
    if shape not in ('Lineal', 'Compuesta', 'Cambio tardío'):
        raise ValueError('Trayectoria no válida.')
    if not all(np.isfinite(v) for v in (initial, change, oscillation)) or initial <= 0 or change <= -100 or oscillation < 0:
        raise ValueError('Usa precios positivos, variación mayor que −100 % y oscilación no negativa.')
    if history.empty or not isinstance(history.index, pd.DatetimeIndex):
        raise ValueError('Se necesita historial fechado.')
    close = history['Close']
    if not np.isfinite(close).all() or (close <= 0).any() or not history.index.is_monotonic_increasing or history.index.has_duplicates:
        raise ValueError('El historial debe tener cierres positivos y fechas ordenadas únicas.')
    # Fechas aproximadas: lunes a viernes, sin calendario de festivos bursátiles.
    dates = pd.bdate_range(history.index[-1].normalize() + pd.Timedelta(days=1),
                          history.index[-1].normalize() + pd.DateOffset(months=months))
    t = np.linspace(0, 1, len(dates) + 1)
    fraction = t ** 2 if shape == 'Cambio tardío' else t
    base = initial * (np.exp(np.log1p(change / 100) * t) if shape == 'Compuesta' else 1 + change / 100 * fraction)
    path = base * np.exp(oscillation / 100 * np.sin(4 * np.pi * t))
    path[0], path[-1] = initial, initial * (1 + change / 100)
    if not np.isfinite(path).all() or (path <= 0).any():
        raise ValueError('Los supuestos producen precios fuera del rango numérico.')
    # Punto inicial hipotético separado: nunca sobrescribe el último cierre real.
    start = pd.DataFrame({'Close': [initial]}, index=[history.index[-1] + pd.Timedelta(seconds=1)])
    future = pd.DataFrame({'Close': path[1:]}, index=dates)
    combined = pd.concat([history[['Close']], start, future])
    result = indicators(combined)
    result['BBMedia'] = result['Close'].rolling(20, min_periods=20).mean()
    deviation = result['Close'].rolling(20, min_periods=20).std(ddof=0)
    result['BBSuperior'] = result['BBMedia'] + 2 * deviation
    result['BBInferior'] = result['BBMedia'] - 2 * deviation
    result['Origen'] = 'Histórico'
    result.loc[start.index[0]:, 'Origen'] = 'Simulado'
    return result


def risk_reward(entry, stop, target, shares=1):
    validate_shares(shares)
    if not all(np.isfinite(v) for v in (entry, stop, target)) or not 0 < stop < entry < target:
        raise ValueError('Para una posición compradora: 0 < stop-loss < entrada < objetivo; cantidad positiva con hasta cuatro decimales.')
    loss, gain = (entry - stop) * shares, (target - entry) * shares
    return {'Pérdida al stop (USD)': loss, 'Ganancia al objetivo (USD)': gain,
            'Beneficio / riesgo': gain / loss}
