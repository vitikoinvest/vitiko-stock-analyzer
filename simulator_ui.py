"""Interfaz del simulador, independiente del análisis histórico existente."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from simulator import simulate, risk_reward
from position import position_values


def render_simulator(prices, symbol, demo):
    st.header('SIMULADOR DE ESCENARIOS DE INVERSIÓN')
    st.warning('SIMULACIÓN HIPOTÉTICA — No es una predicción, recomendación ni orden de inversión.')
    st.caption(f'Base: {"DEMOSTRACIÓN SINTÉTICA" if demo else "historial real de Yahoo Finance"} · {symbol if not demo else "DEMO"} · Última sesión: {prices.index[-1]:%d/%m/%Y}. Usa el ticker del menú lateral para cambiar de acción.')
    st.subheader('MI INVERSIÓN ACTUAL')
    st.caption('Introduce tu posición manualmente. No se conecta ningún broker. Los valores iniciales son un ejemplo editable, no datos de tu cuenta.')
    shares = st.number_input('Número de acciones', min_value=0.0001, value=9.42 if symbol == 'MSFT' else 1.0,
                             step=0.0001, format='%.4f', key=f'position_shares_{symbol}_{demo}')
    average = st.number_input('Mi precio promedio de compra (Average Price)', min_value=0.0001,
                              value=372.42 if symbol == 'MSFT' else float(prices['Close'].iloc[-1]),
                              step=0.01, format='%.4f', key=f'position_average_{symbol}_{demo}')
    st.caption('El costo promedio es independiente del cierre de mercado, del precio inicial hipotético y de la entrada usada para riesgo/beneficio. No se conserva fuera de esta sesión.')
    market = float(prices['Close'].iloc[-1])
    try:
        position = position_values(shares, average, market)
    except ValueError as error:
        st.error(str(error))
        return
    if demo:
        st.warning('MI INVERSIÓN ACTUAL · DEMO: la valoración usa precios sintéticos, no el mercado real.')
    metrics = [
        ('Ticker', 'DEMO' if demo else symbol), ('Cantidad de acciones', f'{shares:,.4f}'),
        ('Precio promedio de compra', f'US$ {average:,.4f}'),
        ('Capital invertido', f'US$ {position["Capital invertido (USD)"]:,.2f}'),
        ('Último cierre disponible' if not demo else 'Último precio DEMO', f'US$ {market:,.2f}'),
        ('Valor actual de la posición', f'US$ {position["Valor actual (USD)"]:,.2f}'),
        ('Ganancia/pérdida no realizada', f'US$ {position["Ganancia/pérdida vs costo promedio (USD)"]:,.2f}'),
        ('Rentabilidad', f'{position["Rentabilidad vs inversión original (%)"]:,.2f} %'),
        ('Precio de equilibrio', f'US$ {position["Precio de equilibrio (USD)"]:,.4f}'),
    ]
    for offset in range(0, len(metrics), 3):
        for column, (label, value) in zip(st.columns(3), metrics[offset:offset+3]):
            column.metric(label, value)
    pnl = position['Ganancia/pérdida vs costo promedio (USD)']
    color = '#4ADE80' if pnl > 0 else '#F87171' if pnl < 0 else '#E2E8F0'
    state = 'Ganancia' if pnl > 0 else 'Pérdida' if pnl < 0 else 'Sin ganancia ni pérdida'
    st.markdown(f'<p style="color:{color};font-weight:600">{state}: US$ {pnl:,.2f} · {position["Rentabilidad vs inversión original (%)"]:,.2f} %</p>', unsafe_allow_html=True)
    st.caption('Valoración al último cierre ajustado disponible, no una cotización en tiempo real. Capital y resultado se calculan sin redondear los valores intermedios; importes mostrados con dos decimales. El equilibrio equivale al costo promedio sin comisiones, impuestos ni dividendos. Los ajustes históricos de Yahoo pueden diferir de los precios de ejecución del broker.')
    st.markdown('Ajusta el precio inicial y los supuestos. Los tres escenarios parten del mismo historial y se recalculan automáticamente.')
    initial = st.number_input('Precio inicial hipotético (USD)', min_value=.01, value=float(prices['Close'].iloc[-1]), key=f'sim_initial_{symbol}_{demo}')
    months = st.selectbox('Horizonte (meses)', [1, 3, 6, 12], index=1)
    shape = st.selectbox('Trayectoria', ['Lineal', 'Compuesta', 'Cambio tardío'])
    oscillation = st.slider('Oscilación de la trayectoria (%)', 0., 50., 0., step=1.)
    st.caption('Lineal: cambio uniforme en precio. Compuesta: cambio porcentual uniforme. Cambio tardío: movimiento concentrado al final. La oscilación añade dos ciclos deterministas en escala logarítmica sin alterar los extremos; no representa volatilidad estimada.')
    cols = st.columns(3)
    changes = {
        'Alcista': cols[0].number_input('Subida total (%)', min_value=0., value=20., step=1.),
        'Bajista': cols[1].number_input('Caída total (%)', min_value=-99.99, max_value=0., value=-20., step=1.),
        'Neutral': cols[2].number_input('Cambio neutral (%)', min_value=-99.99, value=0., step=1.),
    }
    st.caption('Porcentajes respecto al precio inicial manual; el escenario neutral puede ajustarse. La caída debe ser menor del 100 % para conservar precios positivos. Los días futuros son lunes a viernes y pueden incluir festivos bursátiles.')
    colors = {'Alcista': '#4ADE80', 'Bajista': '#F87171', 'Neutral': '#E2E8F0'}
    results = {}
    try:
        for name, change in changes.items():
            results[name] = simulate(prices, initial, change, months, shape, oscillation)
    except ValueError as error:
        st.error(str(error))
        return
    def style(fig):
        fig.update_layout(template='plotly_dark', paper_bgcolor='#0C1424', plot_bgcolor='#172238',
                          font=dict(color='#E2E8F0'), height=650,
                          legend=dict(orientation='h', y=-.15), margin=dict(b=120),
                          hoverlabel=dict(bgcolor='#172238', font_color='#FFFFFF'))
        fig.update_xaxes(gridcolor='#334155', automargin=True)
        fig.update_yaxes(gridcolor='#334155', automargin=True)
        return fig
    comparison = go.Figure()
    comparison.add_trace(go.Scatter(x=prices.tail(126).index, y=prices['Close'].tail(126), name='Histórico DEMO' if demo else 'Histórico REAL', line=dict(color='#FFFFFF')))
    for name, result in results.items():
        future = result[result['Origen'] == 'Simulado']
        comparison.add_trace(go.Scatter(x=future.index, y=future['Close'], name=f'{name} SIMULADO', line=dict(color=colors[name], dash='dash')))
    comparison.update_layout(title='Historial y precios hipotéticos · USD')
    st.plotly_chart(style(comparison), use_container_width=True, theme=None)
    entry = st.number_input('Precio de entrada (USD)', min_value=.01, value=initial, key=f'sim_entry_{symbol}_{demo}')
    stop = st.number_input('Stop-loss (USD)', min_value=.001, value=initial * .9, key=f'sim_stop_{symbol}_{demo}')
    target = st.number_input('Objetivo (USD)', min_value=.01, value=initial * 1.2, key=f'sim_target_{symbol}_{demo}')
    try:
        risk = risk_reward(entry, stop, target, shares)
        for column, (name, value) in zip(st.columns(3), risk.items()):
            column.metric(name, f'{value:,.2f}')
    except ValueError as error:
        st.error(str(error))
    st.caption('Cálculo para una posición compradora, sin comisiones, impuestos ni dividendos. El beneficio/riesgo es la ganancia potencial dividida entre la pérdida potencial. Un stop no garantiza ejecución a ese precio: puede haber saltos y deslizamiento. No se ejecuta ninguna orden.')
    rows = []
    for name, result in results.items():
        last = result.iloc[-1]
        try:
            future_position = position_values(shares, average, market, float(last['Close']))
        except ValueError as error:
            st.error(str(error))
            return
        rows.append({'Escenario SIMULADO': name, 'Cambio desde inicio (%)': changes[name],
                     'Precio final (USD)': last['Close'],
                     **{key: future_position[key] for key in ('Valor futuro hipotético (USD)', 'Ganancia/pérdida vs costo promedio (USD)', 'Rentabilidad vs inversión original (%)', 'Diferencia vs valor actual (USD)')}, 'Ganancia/pérdida vs entrada (USD)': (last['Close'] - entry) * shares,
                     **{field: last[field] for field in ('RSI', 'MACD', 'Signal', 'SMA50', 'SMA100', 'SMA200', 'BBInferior', 'BBMedia', 'BBSuperior')}})
    st.subheader('Comparación al final del horizonte')
    table = pd.DataFrame(rows).set_index('Escenario SIMULADO')
    def result_color(value):
        return 'color: ' + ('#4ADE80' if value > 0 else '#F87171' if value < 0 else '#E2E8F0')
    signed = ['Ganancia/pérdida vs costo promedio (USD)', 'Rentabilidad vs inversión original (%)',
              'Diferencia vs valor actual (USD)', 'Ganancia/pérdida vs entrada (USD)']
    st.dataframe(table.style.format(precision=2, na_rep='No disponible').map(result_color, subset=signed), width='stretch')
    st.caption('Resultados HIPOTÉTICOS sobre tu cantidad y costo promedio. Un escenario alcista puede seguir por debajo de tu costo y uno bajista puede conservar ganancias. La columna vs entrada mantiene el cálculo separado de riesgo/beneficio.')
    selected = st.selectbox('Escenario para explorar indicadores', list(results))
    selected_data = results[selected]
    selected_data = selected_data.loc[prices.index[-min(126, len(prices))]:]
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, row_heights=[.5,.25,.25], vertical_spacing=.08,
                        subplot_titles=('Precio, medias y Bollinger · USD', 'RSI · 14 sesiones', 'MACD · 12/26/9'))
    traces = [('Close',1,'#FFFFFF'),('SMA50',1,'#4ADE80'),('SMA100',1,'#FBBF24'),('SMA200',1,'#C084FC'),
              ('BBInferior',1,'#93C5FD'),('BBMedia',1,'#E2E8F0'),('BBSuperior',1,'#93C5FD'),
              ('RSI',2,'#FBBF24'),('MACD',3,'#93C5FD'),('Signal',3,'#FBBF24'),('Histogram',3,'#4ADE80')]
    for field, row, color in traces:
        for origin, dash in [('Histórico','solid'),('Simulado','dash')]:
            part = selected_data[selected_data['Origen'] == origin]
            fig.add_trace(go.Scatter(x=part.index, y=part[field], name=f'{field} · {origin if not demo else origin + " (base DEMO)"}', line=dict(color=color, dash=dash)), row=row, col=1)
    fig.update_yaxes(range=[0,100], row=2, col=1)
    for value in (30,70):
        fig.add_hline(y=value, row=2, col=1, line_dash='dot', line_color='#E2E8F0')
    st.plotly_chart(style(fig), use_container_width=True, theme=None)
    st.caption('Líneas continuas: indicadores del historial base. Líneas discontinuas: indicadores recalculados con los precios hipotéticos. Bollinger: media de 20 sesiones ± 2 desviaciones estándar poblacionales. Los valores sin historial suficiente quedan como «No disponible». El precio inicial manual añade una observación hipotética inmediatamente después del último cierre real, por lo que su salto también afecta al RSI y MACD. No modifica ni reescala el historial real. No se estima ninguna probabilidad para estos escenarios.')
