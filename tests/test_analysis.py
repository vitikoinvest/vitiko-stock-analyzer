import unittest
import numpy as np
import pandas as pd
from analysis import indicators, levels, trend
from data import demo_prices, validate_ticker

class IndicatorsTest(unittest.TestCase):
    def frame(self, values):
        return pd.DataFrame({'Close': values}, index=pd.bdate_range('2020-01-01', periods=len(values)))

    def test_rising_series(self):
        data = indicators(self.frame(np.arange(1., 301.)))
        self.assertEqual(data['SMA50'].iloc[-1], 275.5)
        self.assertEqual(data['SMA100'].iloc[-1], 250.5)
        self.assertEqual(data['SMA200'].iloc[-1], 200.5)
        self.assertEqual(data['RSI'].iloc[-1], 100)
        self.assertAlmostEqual(data['MACD'].iloc[-1], 7, places=5)
        self.assertEqual(trend(data)[0], 'Alcista')
        self.assertEqual(levels(data), (241., 300.))

    def test_falling_and_flat(self):
        falling = indicators(self.frame(np.arange(300., 0., -1)))
        self.assertEqual(falling['RSI'].iloc[-1], 0)
        self.assertEqual(trend(falling)[0], 'Bajista')
        flat = indicators(self.frame([100.] * 300))
        self.assertEqual(flat['RSI'].iloc[-1], 50)
        self.assertEqual(flat['MACD'].iloc[-1], 0)

    def test_insufficient_history(self):
        data = indicators(self.frame([10., 11., 12.]))
        self.assertTrue(data[['SMA50','SMA100','SMA200','RSI','MACD','Signal']].isna().all().all())
        self.assertEqual(trend(data)[0], 'Datos insuficientes')

    def test_wilder_seed_and_update(self):
        data = indicators(self.frame([100.]+[101.,100.]*7+[102.]))
        self.assertAlmostEqual(data['RSI'].iloc[14],50)
        self.assertAlmostEqual(data['RSI'].iloc[15],100-100/(1+8.5/6.5))

    def test_ticker_and_demo(self):
        self.assertEqual(validate_ticker(' brk-b '),'BRK-B')
        with self.assertRaises(ValueError):
            validate_ticker('../invalid')
        pd.testing.assert_frame_equal(demo_prices(),demo_prices())

if __name__ == '__main__':
    unittest.main()
