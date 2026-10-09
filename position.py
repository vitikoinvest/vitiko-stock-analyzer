"""Valoración de posiciones compradoras, sin comisiones ni ejecución de órdenes."""
from decimal import Decimal, InvalidOperation, localcontext
import math


def positive(value, label):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise ValueError(f'{label} debe ser un número positivo y finito.') from None
    if not number.is_finite() or number <= 0:
        raise ValueError(f'{label} debe ser un número positivo y finito.')
    return number


def validate_shares(value):
    shares = positive(value, 'La cantidad de acciones')
    try:
        rounded = shares.quantize(Decimal('0.0001'))
    except InvalidOperation:
        raise ValueError('La cantidad de acciones excede el rango permitido.') from None
    if shares < Decimal('0.0001') or shares != rounded:
        raise ValueError('La cantidad debe ser al menos 0.0001 y tener como máximo cuatro decimales.')
    return shares


def position_values(shares, average, market, final=None):
    quantity = validate_shares(shares)
    average = positive(average, 'El precio promedio')
    market = positive(market, 'El último cierre')
    final = market if final is None else positive(final, 'El precio final')
    with localcontext() as context:
        context.prec = 40
        invested = quantity * average
        current = quantity * market
        future = quantity * final
        pnl = future - invested
        values = {'Capital invertido (USD)': invested, 'Valor actual (USD)': current,
                  'Valor futuro hipotético (USD)': future,
                  'Ganancia/pérdida vs costo promedio (USD)': pnl,
                  'Rentabilidad vs inversión original (%)': pnl / invested * 100,
                  'Diferencia vs valor actual (USD)': future - current,
                  'Precio de equilibrio (USD)': average}
    result = {key: float(value) for key, value in values.items()}
    if not all(math.isfinite(value) for value in result.values()):
        raise ValueError('Los importes exceden el rango permitido.')
    return result
