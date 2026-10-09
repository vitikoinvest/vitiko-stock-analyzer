import unittest
from position import position_values, validate_shares
from simulator import risk_reward, simulate
from data import demo_prices

class PositionTests(unittest.TestCase):
    def test_microsoft_example(self):
        values = position_values(9.42, 372.42, 400)
        self.assertAlmostEqual(values['Capital invertido (USD)'],3508.1964)
        self.assertEqual(f"{values['Capital invertido (USD)']:,.2f}",'3,508.20')
        self.assertAlmostEqual(values['Valor actual (USD)'],3768)
        self.assertAlmostEqual(values['Ganancia/pérdida vs costo promedio (USD)'],259.8036)
        self.assertAlmostEqual(values['Rentabilidad vs inversión original (%)'],(400/372.42-1)*100)
        self.assertEqual(values['Precio de equilibrio (USD)'],372.42)

    def test_fractions_and_risk(self):
        for shares in (9.42,16.73,11.54,.50,.0001,1.2345):
            self.assertEqual(float(validate_shares(shares)),shares)
            self.assertAlmostEqual(position_values(shares,100,80)['Capital invertido (USD)'],shares*100)
            self.assertAlmostEqual(risk_reward(100,90,120,shares)['Pérdida al stop (USD)'],shares*10)

    def test_profit_loss_and_flat(self):
        for price,profit,percent in [(120,10,20),(80,-10,-20),(100,0,0)]:
            values=position_values(.5,100,price)
            self.assertEqual(values['Ganancia/pérdida vs costo promedio (USD)'],profit)
            self.assertEqual(values['Rentabilidad vs inversión original (%)'],percent)

    def test_scenarios(self):
        history=demo_prices()
        for change in (20,-20,0):
            final=simulate(history,100,change,3)['Close'].iloc[-1]
            values=position_values(.5,100,100,final)
            self.assertAlmostEqual(values['Valor futuro hipotético (USD)'],50*(1+change/100))
            self.assertAlmostEqual(values['Rentabilidad vs inversión original (%)'],change)
            self.assertAlmostEqual(values['Diferencia vs valor actual (USD)'],change*.5)
        # Costo promedio independiente del mercado y del sentido del escenario.
        self.assertLess(position_values(1,200,100,120)['Ganancia/pérdida vs costo promedio (USD)'],0)
        self.assertGreater(position_values(1,50,100,80)['Ganancia/pérdida vs costo promedio (USD)'],0)

    def test_invalid_inputs(self):
        for shares in (0,-1,float('nan'),float('inf'),.00001,1.23456,1e30,'abc'):
            with self.assertRaises(ValueError):
                position_values(shares,100,100)
        for price in (0,-1,float('nan'),float('inf'),'abc'):
            for args in [(1,price,100),(1,100,price),(1,100,100,price)]:
                with self.assertRaises(ValueError):
                    position_values(*args)
