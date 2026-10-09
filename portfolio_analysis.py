"""Métricas descriptivas y alternativas matemáticas; no órdenes ni predicciones."""
import numpy as np
import pandas as pd


def weights(values):
    values = pd.Series(values, dtype=float)
    if values.empty or not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError('Se requieren valores positivos para todas las posiciones.')
    return values / values.sum()


def historical_risk(histories, current_weights):
    prices = pd.concat({symbol: frame['Close'] for symbol, frame in histories.items()}, axis=1)
    prices = prices.sort_index().dropna()
    if len(prices) < 61 or set(prices.columns) != set(current_weights.index):
        raise ValueError('Se necesitan al menos 61 cierres comunes para todas las posiciones.')
    if not np.isfinite(prices).all().all() or (prices <= 0).any().any():
        raise ValueError('Historial no válido.')
    returns = prices.pct_change(fill_method=None).dropna()
    portfolio = returns.mul(current_weights, axis=1).sum(axis=1)
    curve = pd.concat([pd.Series([1.], index=[prices.index[0]]), (1+portfolio).cumprod()])
    drawdown = curve / curve.cummax() - 1
    return {'volatility': float(portfolio.std(ddof=1)*np.sqrt(252)),
            'drawdown': float(drawdown.min()), 'correlation': returns.corr(),
            'curve': curve, 'start': prices.index[0], 'end': prices.index[-1],
            'observations': len(returns)}


def allocation(values, contribution):
    w = weights(values)
    if not np.isfinite(contribution) or contribution < 0:
        raise ValueError('La aportación debe ser finita y no negativa.')
    amounts = w * 0
    # Water filling: iguala posiciones menores antes de aportar a las mayores.
    ordered = sorted(values, key=values.get)
    remaining = float(contribution)
    for n in range(1, len(ordered)+1):
        group = ordered[:n]
        level = float(values[group[-1]])
        needed = float('inf') if n == len(ordered) else (float(values[ordered[n]])-level)*n
        used = min(remaining, needed)
        for symbol in group:
            amounts[symbol] += used/n
        remaining -= used
        if remaining <= 0:
            break
    after = pd.Series(values, dtype=float)+amounts
    return pd.DataFrame({'Valor actual (USD)':pd.Series(values), 'Aportación hipotética (USD)':amounts,
                         'Peso actual (%)':w*100, 'Peso posterior (%)':after/after.sum()*100})


def dividend_estimate(shares, average, market, annual_per_share):
    if annual_per_share is None:
        return None
    if not all(np.isfinite(x) for x in (shares,average,market,annual_per_share)) or min(shares,average,market)<=0 or annual_per_share<0:
        raise ValueError('Valores de dividendos no válidos.')
    annual=shares*annual_per_share
    return {'Anual estimado (USD)':annual,'Promedio mensual (USD)':annual/12,
            'Yield (%)':annual_per_share/market*100,'Yield on cost (%)':annual_per_share/average*100}


def score(max_position, max_sector, volatility, drawdown, limits, importance):
    inputs=[max_position,max_sector,volatility,abs(drawdown)]
    if len(limits)!=4 or len(importance)!=4 or min(limits)<=0 or min(importance)<0 or sum(importance)<=0:
        raise ValueError('Límites positivos y pesos no negativos con suma mayor que cero.')
    if not np.isfinite(inputs+list(limits)+list(importance)).all():
        raise ValueError('Criterios no disponibles.')
    components=[100*max(0.,min(1.,1-value/(2*limit))) for value,limit in zip(inputs,limits)]
    return float(np.average(components,weights=importance)), components
