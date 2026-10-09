import unittest
from unittest.mock import patch
from portfolio import validate_position, import_csv, export_csv, value_portfolio
from streamlit.testing.v1 import AppTest

class PortfolioTests(unittest.TestCase):
    def test_example_and_summary(self):
        item=validate_position(' msft ',9.42,372.42)
        rows, summary=value_portfolio({'MSFT':item},{'MSFT':400})
        self.assertAlmostEqual(summary['capital'],3508.1964)
        self.assertAlmostEqual(summary['valor'],3768)
        self.assertAlmostEqual(summary['resultado'],259.8036)
        self.assertAlmostEqual(summary['rentabilidad'],(400/372.42-1)*100)
        self.assertEqual(rows[0]['Acciones'],9.42)

    def test_partial_and_loss(self):
        positions={ticker:validate_position(ticker,.5,100) for ticker in ('MSFT','META')}
        rows, summary=value_portfolio(positions,{'MSFT':80})
        self.assertEqual(summary['capital'],100)
        self.assertEqual(summary['valor'],40)
        self.assertEqual(summary['resultado'],-10)
        self.assertEqual(summary['rentabilidad'],-20)
        self.assertEqual(summary['faltantes'],['META'])
        self.assertIsNone(rows[1]['Valor actual (USD)'])
        self.assertIsNone(value_portfolio(positions,{})[1]['valor'])

    def test_csv_roundtrip(self):
        positions={'MSFT':validate_position('MSFT',9.42,372.42),'META':validate_position('META',.0001,100)}
        self.assertEqual(import_csv(export_csv(positions)),positions)

    def test_invalid_csv_and_values(self):
        for payload in (b'ticker,acciones,precio_promedio\nMSFT,0,100',
                        b'ticker,acciones,precio_promedio\nMSFT,1.23456,100',
                        b'ticker,acciones,precio_promedio\nMSFT,1,-2',
                        b'ticker,acciones,precio_promedio\nMSFT,1,100\nmsft,2,100',
                        b'ticker,acciones,precio_promedio\nMSFT,1',
                        b'ticker,acciones,precio_promedio\nMSFT,1,100,extra',
                        b'bad,columns\n1,2',b'\xff',b'ticker,acciones,precio_promedio\n'):
            with self.assertRaises(ValueError):
                import_csv(payload)

    def test_ui_edit_delete_and_missing_quote(self):
        from data import demo_prices
        with patch('data.load_prices',return_value=demo_prices()), patch('portfolio_ui.market_quote',side_effect=RuntimeError('Unavailable')):
            app=AppTest.from_file('app.py').run(timeout=30)
            next(x for x in app.text_input if x.label=='Ticker del portafolio').set_value('MSFT')
            next(x for x in app.button if x.label=='Agregar o guardar cambios').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['portfolio_positions']['MSFT']['acciones'],'9.42')
            next(x for x in app.number_input if x.label=='Acciones del portafolio').set_value(.5)
            next(x for x in app.button if x.label=='Agregar o guardar cambios').click().run()
            self.assertEqual(app.session_state['portfolio_positions']['MSFT']['acciones'],'0.5')
            self.assertTrue(any('RESUMEN PARCIAL' in x.value for x in app.warning))
            next(x for x in app.checkbox if x.label.startswith('Confirmo eliminar')).check()
            next(x for x in app.button if x.label=='Eliminar posición').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(app.session_state['portfolio_positions'],{})

    def test_available_quotes_ui_and_failure_independence(self):
        with patch('data.load_prices',side_effect=RuntimeError('Analysis unavailable')), patch('portfolio_ui.market_quote',return_value=(400.,'2026-10-08','2026-10-09T12:00:00+00:00')):
            app=AppTest.from_file('app.py').run(timeout=30)
            next(x for x in app.button if x.label=='Actualizar datos').click().run()
            next(x for x in app.text_input if x.label=='Ticker del portafolio').set_value('MSFT')
            next(x for x in app.button if x.label=='Agregar o guardar cambios').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(app.get('plotly_chart')),3)
            self.assertEqual(len(app.dataframe),1)
            table=app.dataframe[0].value
            self.assertAlmostEqual(table.iloc[0]['Valor actual (USD)'],3768)
            self.assertEqual(table.iloc[0]['Última sesión disponible'],'2026-10-08')
            self.assertEqual(next(x for x in app.metric if x.label=='Capital invertido total').value,'3,508.20')
