import unittest
import json
from copy import deepcopy
from distributions import DEFAULTS, distribution_result, load_manual, validate_record

class DistributionTests(unittest.TestCase):
    def test_fractional_ttms(self):
        for symbol,amount in [('BTCI',10.14),('TLT',3.89)]:
            for shares in (9.42,16.73,.5,.0001):
                result=distribution_result(shares,50,40,DEFAULTS[symbol],999)
                self.assertAlmostEqual(result['Ingreso anual de referencia (USD)'],shares*amount)
                self.assertAlmostEqual(result['Promedio mensual (USD)'],shares*amount/12)
                self.assertAlmostEqual(result['Yield on cost (%)'],amount/50*100)
                self.assertEqual(result['Yield TTM reportado (%)'],DEFAULTS[symbol]['reported_yield'])
                self.assertEqual(result['Fuente'],'Interactive Brokers')

    def test_change_quantity_missing_price(self):
        a=distribution_result(.5,50,None,DEFAULTS['BTCI'])
        b=distribution_result(1.,50,None,DEFAULTS['BTCI'])
        self.assertEqual(b['Ingreso anual de referencia (USD)'],2*a['Ingreso anual de referencia (USD)'])
        self.assertIsNone(a['Yield calculado al cierre (%)'])
        self.assertEqual(a['Yield on cost (%)'],20.28)

    def test_fallback_and_missing(self):
        invalid=dict(DEFAULTS['BTCI'],annual=-1)
        result=distribution_result(1,100,100,invalid,2)
        self.assertEqual(result['Ingreso anual de referencia (USD)'],2)
        self.assertIn('no TTM confirmado',result['Base'])
        self.assertIsNone(distribution_result(1,100,100,None,None))

    def test_json_and_payments(self):
        self.assertEqual(load_manual(json.dumps(DEFAULTS).encode()),DEFAULTS)
        self.assertEqual(DEFAULTS['BTCI']['payment'],.7184)
        self.assertEqual(DEFAULTS['BTCI']['ex_date'],'2026-09-16')
        self.assertIsNone(DEFAULTS['TLT']['payment'])
        for changes in ({'annual':float('nan')},{'source':''},{'updated':'bad'}, {'updated':'2099-01-01'}, {'ex_date':None},{'pay_date':'2026-09-01'}):
            with self.assertRaises(ValueError): validate_record(dict(DEFAULTS['BTCI'],**changes))

    def test_ui_recalculate_and_missing_quotes(self):
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        from data import demo_prices
        with patch('data.load_prices',return_value=demo_prices()),patch('portfolio_ui.market_quote',side_effect=RuntimeError()),patch('intelligent_ui.company_data',side_effect=RuntimeError()):
            app=AppTest.from_file('app.py').run(timeout=30)
            next(x for x in app.text_input if x.label=='Ticker del portafolio').set_value('BTCI')
            next(x for x in app.number_input if x.label=='Acciones del portafolio').set_value(.5)
            next(x for x in app.button if x.label=='Agregar o guardar cambios').click().run()
            next(x for x in app.button if x.label=='Consultar / actualizar análisis inteligente').click().run()
            self.assertFalse(app.exception)
            def distribution_table():
                return next(x.value for x in app.dataframe if 'Ingreso anual de referencia (USD)' in x.value.columns)
            self.assertAlmostEqual(distribution_table().iloc[0]['Ingreso anual de referencia (USD)'],5.07)
            next(x for x in app.number_input if x.label=='Acciones del portafolio').set_value(1.)
            next(x for x in app.button if x.label=='Agregar o guardar cambios').click().run()
            self.assertAlmostEqual(distribution_table().iloc[0]['Ingreso anual de referencia (USD)'],10.14)
            original=deepcopy(app.session_state['portfolio_positions'])
            next(x for x in app.number_input if x.label=='Distribución anual TTM por acción (USD)').set_value(12.)
            next(x for x in app.button if x.label=='Guardar datos de distribuciones').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(distribution_table().iloc[0]['Ingreso anual de referencia (USD)'],12.)
            self.assertEqual(app.session_state['portfolio_positions'],original)
