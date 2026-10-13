"""Solo endpoints gratuitos autorizados. No se registran claves ni mensajes del servidor."""
from dataclasses import dataclass
from collections import deque
from datetime import datetime, timezone
import json
import logging
import math
import threading
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from data import validate_ticker

LOGGER=logging.getLogger(__name__)
ROUTES={'profile':'profile2','metrics':'metric'}
CANDIDATES={
 'P/E TTM':['peTTM'], 'Forward P/E':['forwardPE'], 'PEG':['pegTTM'],
 'EPS TTM':['epsTTM'], 'EPS anual':['epsAnnual'], 'ROE TTM':['roeTTM'],
 'ROIC TTM':['roicTTM'], 'ROA TTM':['roaTTM'], 'Margen bruto TTM':['grossMarginTTM'],
 'Margen operativo TTM':['operatingMarginTTM'], 'Margen neto TTM':['netProfitMarginTTM'],
 'Crecimiento ingresos TTM interanual':['revenueGrowthTTMYoy'],
 'Crecimiento beneficios TTM interanual':['epsGrowthTTMYoy'],
 'Flujo de caja libre TTM':['freeCashFlowTTM'],
 'Deuda/patrimonio trimestral':['totalDebt/totalEquityQuarterly'],
 'Dividendos por acción anual':['dividendPerShareAnnual'],
 'Dividend yield indicativo':['currentDividendYieldTTM'], 'Payout ratio anual':['payoutRatioAnnual'],
}

class ProviderError(Exception):
 def __init__(self,category,status=None,retry_after=0):
  super().__init__(category)
  self.category=category;self.status=status;self.retry_after=retry_after


def transport(key,symbol,endpoint):
 route=ROUTES[endpoint]
 url=f'https://finnhub.io/api/v1/stock/{route}?symbol={symbol}'+('&metric=all' if endpoint=='metrics' else '')
 try:
  with urlopen(Request(url,headers={'X-Finnhub-Token':key,'Accept':'application/json'}),timeout=15) as response:
   result=json.loads(response.read(4_000_000))
 except HTTPError as error:
  status=error.code
  try:wait=max(0,int(error.headers.get('Retry-After','60')))
  except (ValueError,AttributeError):wait=60
  category='autenticación / permisos' if status in (401,403) else 'límite de consultas' if status==429 else 'servidor' if status>=500 else 'error HTTP'
  raise ProviderError(category,status,wait) from None
 except (URLError,TimeoutError,OSError):raise ProviderError('conexión') from None
 except (ValueError,UnicodeError):raise ProviderError('respuesta inválida') from None
 if not isinstance(result,dict) or 'error' in result:
  raise ProviderError('respuesta inválida / error del proveedor')
 if endpoint=='metrics' and 'metric' not in result and result:
  raise ProviderError('respuesta inválida')
 if endpoint=='profile' and result and result.get('ticker') != symbol:
  raise ProviderError('ticker de respuesta incompatible')
 payload=result.get('metric',{}) if endpoint=='metrics' else result
 if not isinstance(payload,dict):raise ProviderError('respuesta inválida')
 # Solo campos permitidos de perfil y valores numéricos de métricas.
 if endpoint=='profile':
  return {field:(payload[field] if isinstance(payload[field],(str,int,float)) and not isinstance(payload[field],bool) and (not key or key not in str(payload[field])) else None) for field in ('name','ticker','currency','exchange','finnhubIndustry','marketCapitalization','shareOutstanding') if field in payload}
 clean = {field:(value if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) else None) for field,value in payload.items() if isinstance(field,str) and field.replace('/','').replace('_','').replace('-','').isalnum() and len(field)<100 and (not key or key not in field)}
 # Mantiene series fiscales explícitas sin asignar sus fechas a métricas snapshot.
 from datetime import date
 series={}
 source_series=result.get('series',{})
 if isinstance(source_series,dict):
  for cadence in ('annual','quarterly'):
   fields=source_series.get(cadence,{})
   if not isinstance(fields,dict):continue
   selected={}
   for field,items in fields.items():
    if not isinstance(field,str) or not field.isalnum() or len(field)>100 or (key and key in field) or not isinstance(items,list):continue
    points=[]
    for item in items[:100]:
     if not isinstance(item,dict):continue
     value=item.get('v')
     if not isinstance(value,(int,float)) or isinstance(value,bool) or not math.isfinite(value):continue
     try:period=date.fromisoformat(item['period']).isoformat()
     except (KeyError,ValueError,TypeError):continue
     points.append({'period':period,'v':value})
    if points:selected[field]=points
   if selected:series[cadence]=selected
 if series:clean['__series__']=series
 return clean


class Budget:
 def __init__(self,clock=time.monotonic):
  self.clock=clock;self.calls=deque();self.blocked_until=0;self.lock=threading.Lock()
 def take(self):
  with self.lock:
   now=self.clock()
   while self.calls and self.calls[0]<=now-60:self.calls.popleft()
   if now<self.blocked_until:raise ProviderError('pausa por límite de consultas',429,self.blocked_until-now)
   if len(self.calls)>=50:raise ProviderError('presupuesto local agotado',429,60)
   self.calls.append(now)
 def pause(self,seconds):
  with self.lock:self.blocked_until=max(self.blocked_until,self.clock()+seconds)


@dataclass
class Result:
 data:dict|None
 fetched_at:str|None
 checked_at:str
 stale:bool=False
 error:str|None=None
 status:int|None=None


class FinnhubProvider:
 def __init__(self,key,budget=None,fetch=transport,clock=time.monotonic,sleep=time.sleep,now=None):
  self._key=key;self.budget=budget or Budget(clock);self.fetch=fetch;self.clock=clock;self.sleep=sleep
  self.now=now or (lambda:datetime.now(timezone.utc).isoformat())
  self.cache={};self.failures={}
 def refresh(self):
  for entry in self.cache.values():entry['expires']=0
 def get(self,symbol,endpoint):
  symbol=validate_ticker(symbol)
  if endpoint not in ROUTES:raise ValueError('Endpoint no autorizado.')
  token=(symbol,endpoint);old=self.cache.get(token);failure=self.failures.get(token)
  if failure and self.clock()<failure['until']:return self._failed(old,failure)
  if old and self.clock()<old['expires']:return Result(dict(old['data']),old['date'],old['date'])
  if not self._key:return Result(None,None,self.now(),error='FINNHUB_API_KEY no configurada')
  for attempt in range(2):
   try:
    self.budget.take()
    data=self.fetch(self._key,symbol,endpoint)
    if not isinstance(data,dict):raise ProviderError('respuesta inválida')
    stamp=self.now()
    self.cache[token]={'data':dict(data),'date':stamp,'expires':self.clock()+(86400 if endpoint=='profile' else 3600) if data else self.clock()+300}
    self.failures.pop(token,None)
    return Result(dict(data),stamp,stamp)
   except Exception as error:
    safe=error if isinstance(error,ProviderError) else ProviderError('error interno de consulta')
    LOGGER.warning('Finnhub ticker=%s endpoint=%s exception=%s http=%s category=%s',symbol,endpoint,type(error).__name__,safe.status,safe.category)
    if safe.status==429:self.budget.pause(max(60,safe.retry_after))
    if attempt==0 and safe.category in ('conexión','servidor'):
     self.sleep(.5);continue
    failure={'until':self.clock()+(max(60,safe.retry_after) if safe.status==429 else 30),'date':self.now(),'error':safe.category,'status':safe.status}
    self.failures[token]=failure
    return self._failed(old,failure)
 @staticmethod
 def _failed(old,failure):
  return Result(dict(old['data']) if old else None,old['date'] if old else None,failure['date'],bool(old),failure['error'],failure['status'])


def metric_rows(data):
 rows=[]
 for label,fields in CANDIDATES.items():
  field=fields[0];value=data.get(field)
  valid=isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
  period='TTM' if 'TTM' in field else 'Anual' if 'Annual' in field else 'Trimestral' if 'Quarterly' in field else 'Estimación futura' if field=='forwardPE' else 'No especificado'
  rows.append({'Indicador':label,'Campo Finnhub':field,'Valor proveedor':value if valid else None,'Período candidato':period,
               'Unidad / definición':'Pendiente de validar','Estado':'Presente · validación económica pendiente' if valid else 'Vacío / inválido' if field in data else 'No devuelto con este nombre'})
 return rows
