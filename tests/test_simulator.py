import unittest
import numpy as np
import pandas as pd
from simulator import simulate, risk_reward
from analysis import indicators
from data import demo_prices

class SimulatorTests(unittest.TestCase):
    def test_horizons_shapes_and_endpoints(self):
        history = demo_prices()
        original = history.copy(deep=True)
        for months in (1,3,6,12):
            for shape in ('Lineal','Compuesta','Cambio tardío'):
                for change in (-99.9,0,25,300):
                    result = simulate(history,100,change,months,shape,10)
                    future = result[result['Origen']=='Simulado']
                    self.assertEqual(future['Close'].iloc[0],100)
                    self.assertAlmostEqual(future['Close'].iloc[-1],100*(1+change/100))
                    self.assertTrue((future['Close']>0).all())
                    self.assertTrue((future.index>history.index[-1]).all())
                    self.assertLessEqual(future.index[-1],history.index[-1]+pd.DateOffset(months=months))
        pd.testing.assert_frame_equal(history,original)

    def test_indicators_and_bollinger(self):
        result=simulate(demo_prices(),123,20,3)
        expected=indicators(result[['Close']])
        pd.testing.assert_frame_equal(result[expected.columns],expected)
        window=result['Close'].tail(20)
        self.assertAlmostEqual(result['BBMedia'].iloc[-1],window.mean())
        self.assertAlmostEqual(result['BBSuperior'].iloc[-1],window.mean()+2*window.std(ddof=0))
        self.assertAlmostEqual(result['BBInferior'].iloc[-1],window.mean()-2*window.std(ddof=0))

    def test_path_assumptions_change_intermediate_values(self):
        history=demo_prices()
        a=simulate(history,100,20,3,'Lineal',0)
        b=simulate(history,100,20,3,'Cambio tardío',15)
        self.assertNotEqual(a['Close'].iloc[-20],b['Close'].iloc[-20])
        self.assertNotEqual(a['RSI'].iloc[-1],b['RSI'].iloc[-1])
        short=simulate(history.head(2),100,0,1)
        self.assertTrue(pd.isna(short['SMA200'].iloc[-1]))

    def test_validation_and_risk(self):
        history=demo_prices()
        for initial,change,months in [(0,20,3),(100,-100,3),(100,float('nan'),3),(100,20,2)]:
            with self.assertRaises(ValueError):
                simulate(history,initial,change,months)
        risk=risk_reward(100,90,120,10)
        self.assertEqual(list(risk.values()),[100,200,2])
        for args in [(100,100,120),(100,90,90),(100,90,120,0)]:
            with self.assertRaises(ValueError):
                risk_reward(*args)

    def test_timezone_preserved(self):
        history=demo_prices().tz_localize('America/New_York')
        result=simulate(history,100,20,3)
        self.assertEqual(str(result.index.tz),'America/New_York')
