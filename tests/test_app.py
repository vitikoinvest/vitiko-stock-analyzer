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
            self.assertEqual(len(app.metric),6)
            self.assertIn('DEMOSTRACIÓN',app.warning[0].value)

    def test_real_display_with_controlled_source(self):
        from data import demo_prices
        with patch('data.load_prices', return_value=demo_prices()):
            app = AppTest.from_file('app.py').run(timeout=30)
            self.assertFalse(app.exception)
            self.assertFalse(app.error)
            self.assertFalse(app.warning)
            self.assertEqual(len(app.metric),6)
            self.assertIn('MSFT',app.subheader[0].value)
            self.assertEqual(len(app.get('plotly_chart')),1)
