import unittest
from unittest.mock import patch
from yahoo_dividends import classify_dividend
from distributions import DEFAULTS,distribution_result

class YahooDividendTests(unittest.TestCase):
    def test_automatic_four_stocks(self):
        # Valores controlados de prueba; no son estimaciones publicadas por la app.
        for symbol in ('MSFT','META','HD','INTU'):
            with self.subTest(symbol=symbol):
                metadata=classify_dividend({'dividendRate':4.,'trailingAnnualDividendRate':3.})
                result=distribution_result(9.42,372.42,400,None,metadata)
                self.assertAlmostEqual(result['Ingreso anual de referencia (USD)'],37.68)
                self.assertIn('indicativa',result['Base'])
                self.assertIn('dividendRate',result['Fuente'])

    def test_fallback_missing_zero_and_invalid(self):
        self.assertEqual(classify_dividend({'trailingAnnualDividendRate':3})['annual'],3)
        self.assertEqual(classify_dividend({'dividendRate':0})['annual'],0)
        for value in (None,True,False,float('nan'),float('inf'),-1,'4'):
            self.assertIsNone(classify_dividend({'dividendRate':value})['annual'])
            self.assertIsNone(distribution_result(1,100,100,None,classify_dividend({'dividendRate':value})))

    def test_manual_priority_and_no_double_count(self):
        for symbol in ('BTCI','TLT'):
            result=distribution_result(.5,100,100,DEFAULTS[symbol],classify_dividend({'dividendRate':999}))
            self.assertEqual(result['Anual por acción (USD)'],DEFAULTS[symbol]['annual'])
            self.assertEqual(result['Ingreso anual de referencia (USD)'],DEFAULTS[symbol]['annual']*.5)

    def test_history_failure_does_not_drop_dividends(self):
        from intelligent_ui import company_data
        company_data.clear()
        with patch('intelligent_ui.load_prices',side_effect=RuntimeError()),patch('intelligent_ui.yf.Ticker') as ticker:
            ticker.return_value.get_info.return_value={'dividendRate':4,'sector':'Technology'}
            history,sector,metadata,stamp=company_data('MSFT')
            self.assertIsNone(history)
            self.assertEqual(metadata['annual'],4)
            self.assertEqual(distribution_result(.5,100,None,None,metadata)['Ingreso anual de referencia (USD)'],2)
        company_data.clear()

    def test_provider_failure_visible(self):
        from intelligent_ui import company_data
        company_data.clear()
        with patch('intelligent_ui.load_prices',side_effect=RuntimeError()),patch('intelligent_ui.yf.Ticker') as ticker:
            ticker.return_value.get_info.side_effect=RuntimeError()
            _,_,metadata,_=company_data('INTU')
            self.assertIsNone(metadata['annual'])
            self.assertIn('falló',metadata['basis'])
        company_data.clear()

    def test_ui_automatic_and_manual_together(self):
        from streamlit.testing.v1 import AppTest
        from data import demo_prices
        frame=demo_prices()
        original={symbol:{'ticker':symbol,'acciones':'0.5','precio_promedio':'100'} for symbol in ('MSFT','META','HD','INTU','BTCI','TLT')}
        with patch('data.load_prices',return_value=frame),patch('portfolio_ui.market_quote',return_value=(100.,'2026-10-13','2026-10-13T12:00:00Z')),patch('intelligent_ui.company_data') as company:
            company.return_value=(frame,'Technology',classify_dividend({'dividendRate':4.}),'2026-10-13T12:00:00Z')
            app=AppTest.from_file('app.py')
            app.session_state['portfolio_positions']=original.copy()
            app.session_state['intelligence_active']=True
            app.run(timeout=30)
            self.assertFalse(app.exception)
            table=next(x.value for x in app.dataframe if 'Ingreso anual de referencia (USD)' in x.value.columns).set_index('Ticker')
            for symbol in ('MSFT','META','HD','INTU'):
                self.assertEqual(table.loc[symbol,'Ingreso anual de referencia (USD)'],2.)
                self.assertIn('indicativa',table.loc[symbol,'Base'])
                self.assertEqual(table.loc[symbol,'Actualización manual'],'No disponible / no aplica')
            self.assertEqual(table.loc['BTCI','Anual por acción (USD)'],10.14)
            self.assertEqual(table.loc['TLT','Anual por acción (USD)'],3.89)
            self.assertEqual(app.session_state['portfolio_positions'],original)
