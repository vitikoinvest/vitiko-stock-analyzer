"""Datos manuales públicos aportados por el usuario, no verificados con un broker."""
import json
from datetime import date
from decimal import Decimal
import math
from position import positive, validate_shares
from data import validate_ticker

DEFAULTS = {
    'BTCI': {'annual':10.14,'reported_yield':30.36,'source':'Interactive Brokers',
             'updated':'2026-10-13','frequency':'No especificada','payment':.7184,
             'ex_date':'2026-09-16','pay_date':'2026-09-18'},
    'TLT': {'annual':3.89,'reported_yield':4.99,'source':'Interactive Brokers',
            'updated':'2026-10-13','frequency':'Mensual','payment':None,'ex_date':None,'pay_date':None},
}


def validate_record(record):
    if not isinstance(record, dict):
        raise ValueError('El registro de distribuciones debe ser un objeto.')
    data = dict(record)
    for field in ('annual','reported_yield','payment'):
        value = data.get(field)
        if field == 'annual' and value is None:
            raise ValueError('La distribución TTM es obligatoria.')
        if value is not None:
            if isinstance(value, bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value < 0:
                raise ValueError('Distribuciones y porcentajes deben ser finitos y no negativos.')
    if not isinstance(data.get('source'),str) or not data['source'].strip():
        raise ValueError('Indica una fuente.')
    def parse_date(field, required=False):
        value = data.get(field)
        if value is None and not required:
            return None
        try:
            if not isinstance(value, str):
                raise ValueError('Se requiere una fecha textual.')
            return date.fromisoformat(value)
        except (TypeError, ValueError) as error:
            raise ValueError(f'Fecha inválida en {field}: usa AAAA-MM-DD.') from error

    updated = parse_date('updated', required=True)
    if updated > date.today():
        raise ValueError('La fecha de actualización no puede ser futura.')
    ex_date = parse_date('ex_date')
    pay_date = parse_date('pay_date')
    if data.get('payment') is not None and (ex_date is None or pay_date is None):
        raise ValueError('Un pago confirmado requiere fecha ex-dividendo y fecha de pago.')
    if data.get('payment') is None and (ex_date is not None or pay_date is not None):
        raise ValueError('Las fechas de pago requieren un importe confirmado.')
    if ex_date is not None and pay_date is not None and pay_date < ex_date:
        raise ValueError('El pago no puede preceder a la fecha ex-dividendo.')
    # Conserva cadenas ISO canónicas para formularios y exportación JSON.
    data['updated'] = updated.isoformat()
    data['ex_date'] = ex_date.isoformat() if ex_date else None
    data['pay_date'] = pay_date.isoformat() if pay_date else None
    return data


def load_manual(payload):
    if len(payload)>100000:
        raise ValueError('El archivo es demasiado grande.')
    try:
        records=json.loads(payload)
        if not isinstance(records,dict) or len(records)>500:
            raise ValueError('Formato de distribuciones no válido.')
        return {validate_ticker(symbol):validate_record(record) for symbol,record in records.items()}
    except (TypeError,KeyError,UnicodeError,json.JSONDecodeError) as error:
        raise ValueError('Archivo de distribuciones no válido.') from error


def distribution_result(shares, average, market, manual=None, yahoo=None):
    quantity=validate_shares(shares)
    average=positive(average,'El costo promedio')
    record=None
    if manual is not None:
        try: record=validate_record(manual)
        except (ValueError,TypeError,KeyError): pass
    yahoo_metadata = yahoo if isinstance(yahoo, dict) else {}
    automatic = yahoo_metadata.get('annual') if isinstance(yahoo, dict) else yahoo
    annual=record['annual'] if record else automatic
    if annual is None or isinstance(annual, bool) or not isinstance(annual,(int,float)) or not math.isfinite(annual) or annual<0:
        return None
    per_share=Decimal(str(annual))
    income=quantity*per_share
    return {'Anual por acción (USD)':annual,'Ingreso anual de referencia (USD)':float(income),
            'Promedio mensual (USD)':float(income/12),
            'Yield calculado al cierre (%)':float(per_share/positive(market,'El cierre')*100) if market is not None else None,
            'Yield on cost (%)':float(per_share/average*100),
            'Yield TTM reportado (%)':record.get('reported_yield') if record else None,
            'Fuente':record['source'] if record else 'Yahoo Finance · ' + str(yahoo_metadata.get('field') or 'dividendRate (no TTM confirmado)'),
            'Base': 'TTM manual aportado por el usuario · no verificado automáticamente' if record else yahoo_metadata.get('basis','Tasa anual reportada, no TTM confirmado'),
            'Actualización manual':record['updated'] if record else None,
            'Frecuencia habitual':record.get('frequency','No especificada') if record else 'No disponible'}
