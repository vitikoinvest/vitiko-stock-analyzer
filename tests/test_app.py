import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

class AppTestCase(unittest.TestCase):
    def test_demo_and_real_failure(self):
        with patch('data.load_prices', side_effect=RuntimeError('Source unavailable')):
            app = AppTest.from_file('app.py').run(timeout=30)
            self.assertFalse(app.exception)
            self.assertTrue(app.error)
            self.assertEqual(len(app.metric),0)
            app.sidebar.radio[0].set_value('Demostración · datos simulados').run()
            self.assertFalse(app.exception)
            self.assertTrue(app.warning)
            self.assertEqual(len(app.metric),18)
            self.assertIn('DEMOSTRACIÓN',app.warning[0].value)

    def test_real_display_with_controlled_source(self):
        from data import demo_prices
        with patch('data.load_prices', return_value=demo_prices()):
            app = AppTest.from_file('app.py').run(timeout=30)
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertEqual(len(app.warning),1)
            self.assertIn('SIMULACIÓN HIPOTÉTICA',app.warning[0].value)
            self.assertEqual(len(app.metric),18)
            self.assertIn('MSFT',app.subheader[0].value)
            self.assertEqual(len(app.get('plotly_chart')),3)

    def test_simulator_controls(self):
        from data import demo_prices
        with patch('data.load_prices', return_value=demo_prices()):
            app = AppTest.from_file('app.py').run(timeout=30)
            next(item for item in app.selectbox if item.label == 'Horizonte (meses)').set_value(12).run(timeout=30)
            next(item for item in app.selectbox if item.label == 'Trayectoria').set_value('Compuesta').run(timeout=30)
            app.slider[0].set_value(15.).run(timeout=30)
            self.assertFalse(app.exception)
            self.assertEqual(len(app.dataframe),1)
            self.assertEqual(len(app.get('plotly_chart')),3)
            stop = next(item for item in app.number_input if item.label == 'Stop-loss (USD)')
            entry = next(item for item in app.number_input if item.label == 'Precio de entrada (USD)')
            stop.set_value(entry.value * 2).run(timeout=30)
            self.assertFalse(app.exception)
            self.assertTrue(app.error)

    def test_fractional_position_and_independent_cost(self):
        from data import demo_prices
        with patch('data.load_prices', return_value=demo_prices()):
            app = AppTest.from_file('app.py').run(timeout=30)
            by_label = lambda label: next(item for item in app.metric if item.label == label)
            self.assertEqual(by_label('Capital invertido').value,'US$ 3,508.20')
            next(item for item in app.number_input if item.label == 'Número de acciones').set_value(.5).run()
            self.assertEqual(by_label('Capital invertido').value,'US$ 186.21')
            next(item for item in app.number_input if item.label == 'Mi precio promedio de compra (Average Price)').set_value(100.).run()
            self.assertEqual(by_label('Capital invertido').value,'US$ 50.00')
            before=by_label('Valor actual de la posición').value
            next(item for item in app.number_input if item.label == 'Precio inicial hipotético (USD)').set_value(200.).run()
            self.assertEqual(by_label('Valor actual de la posición').value,before)
            self.assertEqual(by_label('Capital invertido').value,'US$ 50.00')
            table=app.dataframe[0].value
            self.assertAlmostEqual(table.loc['Alcista','Valor futuro hipotético (USD)'],120)
            self.assertAlmostEqual(table.loc['Alcista','Rentabilidad vs inversión original (%)'],140)
            self.assertFalse(app.exception)
