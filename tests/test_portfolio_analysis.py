import unittest
import numpy as np
import pandas as pd
from portfolio_analysis import weights,historical_risk,allocation,dividend_estimate,score

class IntelligenceTests(unittest.TestCase):
    def test_weights(self):
        w=weights({'MSFT':3508.1964,'META':3508.1964})
        self.assertEqual(w['MSFT'],.5)
        for data in ({},{'A':0},{'A':float('nan')}):
            with self.assertRaises(ValueError): weights(data)

    def test_risk_known_drop(self):
        values=[100.]*61+[80.]*10
        frame=pd.DataFrame({'Close':values},index=pd.bdate_range('2020-01-01',periods=len(values)))
        risk=historical_risk({'A':frame,'B':frame},weights({'A':1,'B':1}))
        self.assertAlmostEqual(risk['drawdown'],-.2)
        self.assertAlmostEqual(risk['correlation'].loc['A','B'],1)
        self.assertAlmostEqual(risk['volatility'],frame['Close'].pct_change().dropna().std()*np.sqrt(252))
        with self.assertRaises(ValueError): historical_risk({'A':frame.head(20)},weights({'A':1}))

    def test_rebalance_conservation(self):
        result=allocation({'A':80,'B':20},40)
        self.assertEqual(result['Aportación hipotética (USD)'].sum(),40)
        self.assertEqual(result.loc['A','Aportación hipotética (USD)'],0)
        self.assertAlmostEqual(result['Peso posterior (%)'].sum(),100)
        self.assertLess(result['Peso posterior (%)'].max(),80)
        equal=allocation({'A':80,'B':20},100)
        self.assertEqual(equal.loc['A','Peso posterior (%)'],50)
        self.assertEqual(allocation({'A':80},20).loc['A','Peso posterior (%)'],100)
        with self.assertRaises(ValueError): allocation({'A':80},-1)

    def test_dividends(self):
        values=dividend_estimate(9.42,372.42,400,4)
        self.assertEqual(values['Anual estimado (USD)'],37.68)
        self.assertAlmostEqual(values['Promedio mensual (USD)'],3.14)
        self.assertEqual(values['Yield (%)'],1)
        self.assertAlmostEqual(values['Yield on cost (%)'],4/372.42*100)
        self.assertIsNone(dividend_estimate(1,100,100,None))
        self.assertEqual(dividend_estimate(1,100,100,0)['Anual estimado (USD)'],0)
        with self.assertRaises(ValueError): dividend_estimate(1,100,100,-1)

    def test_score_transparency(self):
        number,parts=score(.2,.35,.25,-.3,[.2,.35,.25,.3],[1,1,1,1])
        self.assertEqual(number,50)
        self.assertEqual(parts,[50]*4)
        self.assertEqual(score(0,0,0,0,[1]*4,[1]*4)[0],100)
        self.assertEqual(score(2,2,2,-2,[1]*4,[1]*4)[0],0)
        with self.assertRaises(ValueError): score(0,0,0,0,[1]*4,[0]*4)

    def test_ui_complete_and_missing_sector(self):
        from unittest.mock import patch
        from streamlit.testing.v1 import AppTest
        from data import demo_prices
        frame=demo_prices()
        with patch('data.load_prices',return_value=frame), patch('portfolio_ui.market_quote',return_value=(400.,'2026-10-08','2026-10-09T12:00:00Z')), patch('intelligent_ui.company_data') as company:
            company.return_value=(frame,'Tecnología',4.,'2026-10-09T12:00:00Z')
            app=AppTest.from_file('app.py').run(timeout=30)
            next(x for x in app.text_input if x.label=='Ticker del portafolio').set_value('MSFT')
            next(x for x in app.button if x.label=='Agregar o guardar cambios').click().run()
            # Mock de función con caché: conserva la operación clear requerida por el botón.
            next(x for x in app.button if x.label=='Consultar / actualizar análisis inteligente').click().run(timeout=30)
            self.assertFalse(app.exception)
            self.assertTrue(any(x.label=='Puntuación descriptiva' for x in app.metric))
            next(x for x in app.number_input if x.label=='Aportación adicional hipotética (USD)').set_value(500.).run()
            self.assertFalse(app.exception)
            company.return_value=(frame,None,None,'2026-10-09T12:00:00Z')
            app.run()
            self.assertFalse(app.exception)
            self.assertFalse(any(x.label=='Puntuación descriptiva' for x in app.metric))
            self.assertTrue(any('Puntuación no disponible' in x.value for x in app.warning))
