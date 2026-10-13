import unittest
from types import SimpleNamespace
from unittest.mock import Mock
from yahoo_metadata import MetadataClient, classify_error

class HTTPError(Exception):
    def __init__(self,status):
        self.response=SimpleNamespace(status_code=status)

class MetadataTests(unittest.TestCase):
    def client(self,fetch):
        self.time=0
        self.sleep=Mock()
        return MetadataClient(fetch,clock=lambda:self.time,sleep=self.sleep,now=lambda:f'date-{self.time}')

    def test_http_classes_retry_and_cooldown(self):
        for status,category,attempts in [(401,'autenticación / acceso denegado',1),(403,'autenticación / acceso denegado',1),(429,'límite de consultas',2)]:
            fetch=Mock(side_effect=HTTPError(status))
            client=self.client(fetch)
            result=client.get('MSFT')
            self.assertEqual(result.http_status,status)
            self.assertEqual(result.error,category)
            self.assertEqual(fetch.call_count,attempts)
            client.refresh();client.get('MSFT')
            self.assertEqual(fetch.call_count,attempts)
            fetch.side_effect=None;fetch.return_value={'sector':'Technology','dividendRate':4.}
            self.time=121
            self.assertIsNone(client.get('MSFT').error)

    def test_connection_then_recovery(self):
        fetch=Mock(side_effect=[ConnectionError('secret'),{'dividendRate':4.}])
        client=self.client(fetch)
        self.assertEqual(client.get('META').info['dividendRate'],4)
        self.sleep.assert_called_once_with(.5)
        client.get('META');self.assertEqual(fetch.call_count,2)

    def test_invalid_response_and_missing_fields(self):
        for value in (None,[],{},'bad'):
            client=self.client(Mock(return_value=value))
            result=client.get('HD')
            self.assertEqual(result.error,'respuesta inválida')
            self.assertIsNone(result.info)
        client=self.client(Mock(return_value={'symbol':'SOFI'}))
        self.assertIsNone(client.get('SOFI').error)
        self.assertEqual(client.get('SOFI').info,{'symbol':'SOFI'})

    def test_last_good_stale_and_recovery(self):
        fetch=Mock(return_value={'sector':'Technology','dividendRate':4.})
        client=self.client(fetch)
        good=client.get('INTU')
        fetch.side_effect=HTTPError(403)
        self.time=3601
        failed=client.get('INTU')
        self.assertTrue(failed.stale)
        self.assertEqual(failed.info,good.info)
        self.assertEqual(failed.fetched_at,good.fetched_at)
        self.assertEqual(failed.checked_at,'date-3601')
        self.time=3632;fetch.side_effect=None;fetch.return_value={'sector':'Technology','dividendRate':5.}
        self.assertFalse(client.get('INTU').stale)
        self.assertEqual(client.get('INTU').info['dividendRate'],5)

    def test_logs_exclude_sensitive_message(self):
        client=self.client(Mock(side_effect=ConnectionError('cookie=SECRET url=private account=123')))
        with self.assertLogs('yahoo_metadata',level='WARNING') as logs:client.get('MSFT')
        text=' '.join(logs.output)
        self.assertIn('ticker=MSFT',text)
        self.assertIn('ConnectionError',text)
        self.assertNotIn('SECRET',text)
        self.assertNotIn('account',text)

    def test_http_500_and_wrapped_status(self):
        error=RuntimeError();error.__cause__=HTTPError(401)
        self.assertEqual(classify_error(error)[1],401)
        fetch=Mock(side_effect=[HTTPError(503),{'sector':'Technology'}])
        self.assertIsNone(self.client(fetch).get('MSFT').error)
        self.assertEqual(fetch.call_count,2)

    def test_progressive_connection_backoff(self):
        fetch=Mock(side_effect=ConnectionError())
        client=self.client(fetch)
        client.get('MSFT')
        self.assertEqual(fetch.call_count,3)
        self.assertEqual([call.args[0] for call in self.sleep.call_args_list],[.5,1.])

    def test_ui_stale_labels_and_manual_priority(self):
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        from data import demo_prices
        metadata={'annual':4.,'field':'dividendRate','basis':'Tasa anual indicativa · DESACTUALIZADO',
                  'fetched_at':'2026-10-12T12:00:00Z','checked_at':'2026-10-13T12:00:00Z',
                  'stale':True,'error':'autenticación / acceso denegado','exception_type':'HTTPError','http_status':403}
        positions={symbol:{'ticker':symbol,'acciones':'.5','precio_promedio':'100'} for symbol in ('MSFT','BTCI')}
        with patch('data.load_prices',return_value=demo_prices()),patch('portfolio_ui.market_quote',return_value=(100.,'2026-10-13','2026-10-13T12:00:00Z')),patch('intelligent_ui.company_data',return_value=(demo_prices(),'Technology',metadata,metadata['fetched_at'])):
            app=AppTest.from_file('app.py')
            app.session_state['portfolio_positions']=positions.copy()
            app.session_state['intelligence_active']=True
            app.run(timeout=30)
            self.assertFalse(app.exception)
            self.assertTrue(any('HTTP 403' in warning.value and 'DESACTUALIZADO' in warning.value for warning in app.warning))
            table=next(item.value for item in app.dataframe if 'Estado Yahoo' in item.value.columns).set_index('Ticker')
            self.assertEqual(table.loc['MSFT','Estado Yahoo'],'Desactualizado')
            self.assertEqual(table.loc['MSFT','Fecha Yahoo UTC'],metadata['fetched_at'])
            self.assertEqual(table.loc['BTCI','Anual por acción (USD)'],10.14)
            self.assertEqual(table.loc['BTCI','Estado Yahoo'],'No aplica · prioridad manual')
            self.assertEqual(app.session_state['portfolio_positions'],positions)
