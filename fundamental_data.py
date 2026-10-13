"""Contratos explícitos: no convertir una convención candidata en dato validado."""
from dataclasses import dataclass
from datetime import date
import math

@dataclass(frozen=True)
class Contract:
    label: str
    unit: str
    period: str
    definition: str

CONTRACTS = {
    'peTTM': Contract('P/E', 'multiple', 'TTM', 'Precio dividido entre beneficios por acción TTM; base EPS del proveedor pendiente de confirmar.'),
    'forwardPE': Contract('Forward P/E', 'multiple', 'forward', 'Precio dividido entre EPS estimado; horizonte y consenso pendientes.'),
    'pegTTM': Contract('PEG', 'ratio', 'TTM', 'P/E respecto al crecimiento; ventana y escala de crecimiento pendientes.'),
    'epsTTM': Contract('EPS', 'currency_per_share', 'TTM', 'Beneficio por acción; dilución y exclusión de extraordinarios pendientes.'),
    'epsAnnual': Contract('EPS', 'currency_per_share', 'annual', 'EPS anual; ejercicio y base contable pendientes.'),
    'roeTTM': Contract('ROE', 'percent_points', 'TTM', 'Beneficio sobre patrimonio; denominador medio/final pendiente.'),
    'roaTTM': Contract('ROA', 'percent_points', 'TTM', 'Beneficio sobre activos; denominador medio/final pendiente.'),
    'grossMarginTTM': Contract('Margen bruto', 'percent_points', 'TTM', 'Beneficio bruto sobre ingresos.'),
    'operatingMarginTTM': Contract('Margen operativo', 'percent_points', 'TTM', 'Resultado operativo sobre ingresos; ajustes pendientes.'),
    'netProfitMarginTTM': Contract('Margen neto', 'percent_points', 'TTM', 'Beneficio neto sobre ingresos; base pendiente.'),
    'currentDividendYieldTTM': Contract('Dividend yield', 'percent_points', 'TTM', 'Dividendos sobre precio; ventana y precio de referencia pendientes.'),
    'payoutRatioAnnual': Contract('Payout ratio', 'percent_points', 'annual', 'Dividendos respecto a beneficios; denominador pendiente.'),
}


def finite(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)


def normalize_finnhub(data, fetched_at, currency=None, approvals=None, stale=False):
    """approvals: evidencia externa por campo {unit, period, reference, definition}.

    Sin aprobación completa no hay valor normalizado utilizable. No infiere moneda,
    fechas económicas, EPS equivalente, Forward P/E ni ratios de otras fuentes.
    """
    approvals=approvals or {}
    rows=[]
    for field, contract in CONTRACTS.items():
        raw=data.get(field)
        available=finite(raw)
        approval=approvals.get(field,{})
        verified=(approval.get('unit')==contract.unit and approval.get('period')==contract.period
                  and isinstance(approval.get('reference'),str) and bool(approval['reference'].strip())
                  and isinstance(approval.get('definition'),str) and bool(approval['definition'].strip()))
        if contract.unit=='currency_per_share' and not currency:verified=False
        normalized=None
        if available and verified:
            normalized=raw/100 if contract.unit=='percent_points' else float(raw)
        status=('missing' if field not in data else 'invalid_or_empty' if not available
                else 'validated_contract' if verified else 'pending_contract')
        rows.append({'field':field,'indicator':contract.label,'raw_value':raw if available else None,
                     'normalized_value':normalized,'proposed_source_unit':contract.unit,
                     'normalized_unit':'fraction' if contract.unit=='percent_points' else contract.unit,
                     'period_kind':contract.period,'economic_date':None,'currency':currency if contract.unit=='currency_per_share' else None,
                     'source':'Finnhub','endpoint':'stock/metric','fetched_at':fetched_at,
                     'stale':stale,'status':status,'valuation_ready':False,
                     'definition':approval.get('definition',contract.definition),
                     'validation_reference':approval.get('reference') if verified else None})
    return rows


def series_rows(data,fetched_at,stale=False):
    """Fechas entregadas en series: nunca atribuirlas a snapshots TTM/anuales."""
    rows=[]
    for cadence, fields in data.get('__series__',{}).items():
        if cadence not in ('annual','quarterly') or not isinstance(fields,dict):continue
        for field, values in fields.items():
            if not isinstance(values,list):continue
            for item in values:
                if not isinstance(item,dict) or not finite(item.get('v')):continue
                try: period=date.fromisoformat(item['period']).isoformat()
                except (KeyError,ValueError,TypeError):continue
                rows.append({'source':'Finnhub','field':field,'raw_value':item['v'],
                             'economic_date':period,'period_kind':cadence,'fetched_at':fetched_at,
                             'unit':'unknown','status':'reported_series_pending_definition','stale':stale})
    return rows
