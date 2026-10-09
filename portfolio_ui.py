"""Interfaz privada por sesión; la caché almacena solo precios públicos."""
from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data import load_prices
from portfolio import validate_position, import_csv, export_csv, value_portfolio


@st.cache_data(ttl=900, show_spinner=False)
def market_quote(symbol):
    prices = load_prices(symbol)
    return float(prices['Close'].iloc[-1]), prices.index[-1].date().isoformat(), datetime.now(timezone.utc).isoformat()


def render_portfolio():
    st.header('MI PORTAFOLIO')
    st.caption('Registro manual privado por sesión. No se guarda en GitHub ni en archivos del servidor. Exporta tu CSV antes de cerrar: la sesión puede perderse. No se conectan cuentas ni se ejecutan operaciones.')
    positions = st.session_state.setdefault('portfolio_positions', {})
    with st.form('portfolio_edit'):
        ticker = st.text_input('Ticker del portafolio', placeholder='MSFT')
        shares = st.number_input('Acciones del portafolio', min_value=.0001, value=9.42, step=.0001, format='%.4f')
        average = st.number_input('Precio promedio del portafolio (USD)', min_value=.0001, value=372.42, format='%.4f')
        save = st.form_submit_button('Agregar o guardar cambios')
    if save:
        try:
            item = validate_position(ticker, shares, average)
            if len(positions) >= 500 and item['ticker'] not in positions:
                raise ValueError('Máximo 500 posiciones.')
            positions[item['ticker']] = item
            st.success('Posición guardada en esta sesión. Para editarla, introduce su ticker y los nuevos valores.')
        except ValueError as error:
            st.error(str(error))
    if positions:
        with st.form('portfolio_delete'):
            selected = st.selectbox('Posición para eliminar', list(positions))
            confirmation = st.checkbox('Confirmo eliminar esta posición de la sesión')
            remove = st.form_submit_button('Eliminar posición')
        if remove:
            if confirmation:
                del positions[selected]
                st.rerun()
            else:
                st.warning('Marca la confirmación para eliminar la posición.')
    upload = st.file_uploader('Importar copia CSV privada', type=['csv'])
    st.caption('Columnas: ticker,acciones,precio_promedio. Usa punto decimal. Importar agrega posiciones y actualiza los tickers coincidentes; conserva los demás. No subas el CSV a GitHub.')
    if st.button('Importar posiciones'):
        try:
            if upload is None:
                raise ValueError('Selecciona primero un CSV.')
            incoming = import_csv(upload.getvalue())
            if len(set(positions) | set(incoming)) > 500:
                raise ValueError('Máximo 500 posiciones.')
            positions.update(incoming)
            st.success('Importación completa. Las posiciones solo se conservan en esta sesión.')
            st.rerun()
        except ValueError as error:
            st.error(str(error))
    st.download_button('Exportar mi copia CSV', data=export_csv(positions), file_name='mi_portafolio.csv', mime='text/csv')
    if not positions:
        st.info('Agrega tu primera posición. Ejemplo: MSFT, 9.42 acciones y costo promedio 372.42.')
        return
    if st.button('Actualizar precios del portafolio'):
        market_quote.clear()
    quotes, metadata = {}, {}
    with st.spinner('Consultando cierres de Yahoo Finance…'):
        for symbol in positions:
            try:
                quotes[symbol], session, fetched = market_quote(symbol)
                metadata[symbol] = (session, fetched)
            except Exception:
                st.warning(f'{symbol}: precio no disponible. No se sustituye por datos simulados.')
    rows, summary = value_portfolio(positions, quotes)
    if summary['faltantes']:
        st.warning('RESUMEN PARCIAL: valor, resultado y rentabilidad incluyen solo posiciones con precio. El capital invertido incluye todas. Faltan: ' + ', '.join(summary['faltantes']))
    metrics = [('Capital invertido total', summary['capital']), ('Valor disponible (USD)', summary['valor']),
               ('Ganancia/pérdida disponible (USD)', summary['resultado']), ('Rentabilidad disponible (%)', summary['rentabilidad'])]
    for column, (label, value) in zip(st.columns(4), metrics):
        column.metric(label, 'No disponible' if value is None else f'{value:,.2f}')
    st.caption('Rentabilidad agregada = resultado disponible / costo de las posiciones con precio × 100. Sin comisiones, impuestos ni dividendos. Cierres ajustados, no precios en tiempo real; consulta en caché hasta 15 minutos.')
    table = pd.DataFrame(rows)
    table['Última sesión disponible'] = table['Ticker'].map(lambda symbol: metadata.get(symbol, ('No disponible', 'No disponible'))[0])
    table['Consulta (UTC)'] = table['Ticker'].map(lambda symbol: metadata.get(symbol, ('No disponible', 'No disponible'))[1])
    def color(value):
        return 'color: ' + ('#E2E8F0' if pd.isna(value) or value == 0 else '#4ADE80' if value > 0 else '#F87171')
    formats = {key: '{:,.2f}' for key in table.select_dtypes('number').columns}
    formats['Acciones'] = '{:,.4f}'
    st.dataframe(table.style.format(formats, na_rep='No disponible').map(color, subset=['Ganancia/pérdida (USD)', 'Rentabilidad (%)']), width='stretch')
    available = table.dropna(subset=['Valor actual (USD)'])
    figures = [go.Figure(go.Pie(labels=table['Ticker'], values=table['Capital invertido (USD)'], hole=.4))]
    titles = ['Distribución por capital invertido · todas las posiciones']
    if not available.empty:
        figures.extend([go.Figure(go.Pie(labels=available['Ticker'], values=available['Valor actual (USD)'], hole=.4)),
                        go.Figure(go.Bar(x=available['Ticker'], y=available['Ganancia/pérdida (USD)'], marker_color=['#4ADE80' if value >= 0 else '#F87171' for value in available['Ganancia/pérdida (USD)']]))])
        titles.extend(['Distribución por valor disponible · parcial si faltan precios', 'Ganancias y pérdidas por posición · USD, solo precios disponibles'])
    for figure, title in zip(figures, titles):
        figure.update_layout(title=title, template='plotly_dark', paper_bgcolor='#0C1424', plot_bgcolor='#172238', font=dict(color='#E2E8F0'), legend=dict(orientation='h'))
        st.plotly_chart(figure, use_container_width=True, theme=None)
    from intelligent_ui import render_intelligence
    with st.expander('ANÁLISIS INTELIGENTE DE PORTAFOLIO', expanded=False):
        render_intelligence(positions, quotes)
