"""Clasificación de campos reales de Yahoo; nunca deduce dividendos del yield."""
import math


def classify_dividend(info):
    for field, basis in [('dividendRate','Tasa anual indicativa · Yahoo Finance'),
                         ('trailingAnnualDividendRate','TTM reportado por Yahoo · no verificado independientemente')]:
        value=info.get(field)
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            continue
        return {'annual':float(value),'field':field,'basis':basis}
    return {'annual':None,'field':None,'basis':'No disponible: Yahoo no devolvió una tasa válida'}
