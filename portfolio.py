"""Posiciones en memoria e intercambio CSV, sin persistencia en disco."""
import csv
from io import StringIO
from decimal import Decimal
from data import validate_ticker
from position import positive, validate_shares, position_values

FIELDS = ['ticker', 'acciones', 'precio_promedio']


def validate_position(ticker, shares, average):
    symbol = validate_ticker(str(ticker))
    quantity = validate_shares(shares)
    cost = positive(average, 'El precio promedio')
    position_values(quantity, cost, cost)  # Valida también rango numérico.
    return {'ticker': symbol, 'acciones': str(quantity), 'precio_promedio': str(cost)}


def import_csv(payload):
    if len(payload) > 1_000_000:
        raise ValueError('El CSV debe ocupar menos de 1 MB.')
    try:
        text = payload.decode('utf-8-sig')
        reader = csv.DictReader(StringIO(text), strict=True)
        if reader.fieldnames != FIELDS:
            raise ValueError('Columnas requeridas, en orden: ticker,acciones,precio_promedio.')
        positions = {}
        for number, row in enumerate(reader, start=2):
            if number > 501:
                raise ValueError('Máximo 500 posiciones.')
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f'Fila {number}: faltan o sobran campos.')
            item = validate_position(row['ticker'], row['acciones'], row['precio_promedio'])
            if item['ticker'] in positions:
                raise ValueError(f'Fila {number}: ticker duplicado.')
            positions[item['ticker']] = item
        if not positions:
            raise ValueError('El CSV no contiene posiciones.')
        return positions
    except (UnicodeError, csv.Error) as error:
        raise ValueError('CSV no válido; utiliza UTF-8 y comas como separador.') from error


def export_csv(positions):
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=FIELDS)
    writer.writeheader()
    for item in positions.values():
        writer.writerow(validate_position(item['ticker'], item['acciones'], item['precio_promedio']))
    return output.getvalue().encode('utf-8')


def value_portfolio(positions, quotes):
    rows = []
    invested = Decimal('0')
    covered_cost = covered_value = Decimal('0')
    missing = []
    for symbol, item in positions.items():
        valid = validate_position(symbol, item['acciones'], item['precio_promedio'])
        cost = Decimal(valid['acciones']) * Decimal(valid['precio_promedio'])
        invested += cost
        quote = quotes.get(symbol)
        row = {'Ticker': symbol, 'Acciones': float(valid['acciones']),
               'Precio promedio (USD)': float(valid['precio_promedio']), 'Capital invertido (USD)': float(cost)}
        if quote is None:
            missing.append(symbol)
            row.update({'Último cierre (USD)': None, 'Valor actual (USD)': None,
                        'Ganancia/pérdida (USD)': None, 'Rentabilidad (%)': None})
        else:
            values = position_values(valid['acciones'], valid['precio_promedio'], quote)
            covered_cost += cost
            covered_value += Decimal(valid['acciones']) * positive(quote, 'El cierre')
            row.update({'Último cierre (USD)': float(quote), 'Valor actual (USD)': values['Valor actual (USD)'],
                        'Ganancia/pérdida (USD)': values['Ganancia/pérdida vs costo promedio (USD)'],
                        'Rentabilidad (%)': values['Rentabilidad vs inversión original (%)']})
        rows.append(row)
    pnl = covered_value - covered_cost
    summary = {'capital': float(invested), 'valor': float(covered_value) if covered_cost else None,
               'resultado': float(pnl) if covered_cost else None,
               'rentabilidad': float(pnl / covered_cost * 100) if covered_cost else None,
               'faltantes': missing}
    return rows, summary
