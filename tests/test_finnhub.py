import unittest
from unittest.mock import Mock,patch
from urllib.error import HTTPError,URLError
from finnhub_provider import FinnhubProvider,Budget,ProviderError,transport,metric_rows

class FinnhubTests(unittest.TestCase):
 def provider(self,fetch):
  self.time=0
  return FinnhubProvider('TEST_SECRET',fetch=fetch,clock=lambda:self.time,sleep=Mock(),now=lambda:str(self.time))
 def test_two_endpoints_only_and_cache(self):
  fetch=Mock(return_value={'peTTM':30})
  p=self.provider(fetch)
  p.get('MSFT','profile');p.get('MSFT','metrics');p.get('MSFT','metrics')
  self.assertEqual(fetch.call_count,2)
  with self.assertRaises(ValueError):p.get('MSFT','dividends')
 def test_failures_and_recovery(self):
  for status in (401,403,429):
   fetch=Mock(side_effect=ProviderError('auth' if status!=429 else 'límite de consultas',status))
   p=self.provider(fetch)
   first=p.get('MSFT','metrics')
   self.assertEqual(first.status,status)
   p.refresh();p.get('MSFT','metrics');self.assertEqual(fetch.call_count,1)
   self.time=121;fetch.side_effect=None;fetch.return_value={'peTTM':20}
   self.assertIsNone(p.get('MSFT','metrics').error)
 def test_connection_retry_stale(self):
  fetch=Mock(return_value={'peTTM':20})
  p=self.provider(fetch);first=p.get('MSFT','metrics')
  self.time=3601;fetch.side_effect=ProviderError('conexión')
  result=p.get('MSFT','metrics')
  self.assertTrue(result.stale);self.assertEqual(result.data,first.data)
  self.assertEqual(result.fetched_at,first.fetched_at);self.assertEqual(fetch.call_count,3)
 def test_budget_shared(self):
  self.time=0;budget=Budget(lambda:self.time)
  for _ in range(50):budget.take()
  with self.assertRaises(ProviderError):budget.take()
  self.time=61;budget.take()
 def test_units_missing_not_zero(self):
  rows=metric_rows({'peTTM':0,'epsTTM':None,'roeTTM':True,'forwardPE':30})
  by={row['Indicador']:row for row in rows}
  self.assertEqual(by['P/E TTM']['Valor proveedor'],0)
  self.assertIsNone(by['EPS TTM']['Valor proveedor'])
  self.assertIsNone(by['ROE TTM']['Valor proveedor'])
  self.assertEqual(by['Forward P/E']['Período candidato'],'Estimación futura')
  self.assertEqual(by['Forward P/E']['Unidad / definición'],'Pendiente de validar')
 def test_transport_errors_sanitized(self):
  for status in (401,403,429):
   with patch('finnhub_provider.urlopen',side_effect=HTTPError('https://private?token=TEST_SECRET',status,'TEST_SECRET',{},None)):
    with self.assertRaises(ProviderError) as caught:transport('TEST_SECRET','MSFT','profile')
    self.assertNotIn('TEST_SECRET',str(caught.exception))
    self.assertEqual(caught.exception.status,status)
  with patch('finnhub_provider.urlopen',side_effect=URLError('TEST_SECRET')):
   with self.assertRaises(ProviderError) as caught:transport('TEST_SECRET','MSFT','metrics')
   self.assertEqual(str(caught.exception),'conexión')
 def test_invalid_response_and_logs(self):
  p=self.provider(Mock(side_effect=RuntimeError('TEST_SECRET')))
  with self.assertLogs('finnhub_provider',level='WARNING') as logs:p.get('MSFT','metrics')
  self.assertNotIn('TEST_SECRET',' '.join(logs.output))
  response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
  response.read.return_value=b'null'
  with patch('finnhub_provider.urlopen',return_value=response):
   with self.assertRaises(ProviderError):transport('TEST_SECRET','MSFT','metrics')
 def test_free_headers_and_payload(self):
  response=Mock();response.__enter__=Mock(return_value=response);response.__exit__=Mock(return_value=False)
  response.read.return_value=b'{"metric":{"peTTM":30,"bad":"TEST_SECRET"}}'
  with patch('finnhub_provider.urlopen',return_value=response) as opening:
   self.assertEqual(transport('TEST_SECRET','MSFT','metrics'),{'peTTM':30,'bad':None})
   request=opening.call_args.args[0]
   self.assertNotIn('TEST_SECRET',request.full_url)
   self.assertIn('/stock/metric?',request.full_url)
 def test_ui_no_private_mutation_etfs_excluded(self):
  from streamlit.testing.v1 import AppTest
  from data import demo_prices
  positions={symbol:{'ticker':symbol,'acciones':'.5','precio_promedio':'100'} for symbol in ('MSFT','BTCI','TLT')}
  with patch('data.load_prices',return_value=demo_prices()),patch('portfolio_ui.market_quote',return_value=(100.,'2026-10-13','now')),patch('finnhub_ui._key',return_value='TEST_SECRET'),patch('intelligent_ui.company_data',return_value=(demo_prices(),'Technology',4.,'date')),patch('finnhub_provider.transport',return_value={'peTTM':20}) as api:
   # Inject client: default fetch argument is bound at definition time.
   client=self.provider(api)
   app=AppTest.from_file('app.py')
   app.session_state['portfolio_positions']=positions.copy()
   app.session_state['finnhub_provider']=client
   app.session_state['intelligence_active']=True
   app.run(timeout=30)
   next(x for x in app.checkbox if x.label=='Activar consultas Finnhub para esta sesión').check().run()
   self.assertFalse(app.exception)
   self.assertEqual(api.call_count,2)
   self.assertTrue(all(call.args[1]=='MSFT' for call in api.call_args_list))
   self.assertEqual(app.session_state['portfolio_positions'],positions)
   self.assertEqual(app.session_state['manual_distributions']['BTCI']['annual'],10.14)
   self.assertEqual(app.session_state['manual_distributions']['TLT']['annual'],3.89)
