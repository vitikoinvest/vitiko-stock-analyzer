from datetime import datetime, timezone
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from data import load_prices
from portfolio_analysis import weights, historical_risk, allocation, dividend_estimate, score


@st.cache_data(ttl=3600, show_spinner=False)
def company_data(symbol):
    history=load_prices(symbol)
    history=history.copy()
    history.index=pd.to_datetime(history.index.date)
    sector=None
    annual=None
    try:
        info=yf.Ticker(symbol).get_info()
        sector=info.get('sector') or None
        value=info.get('dividendRate')
        if isinstance(value,(int,float)) and np.isfinite(value) and value>=0:
            annual=float(value)
    except Exception:
        pass
    return history, sector, annual, datetime.now(timezone.utc).isoformat()


def render_intelligence(positions, quotes):
    st.header('ANÁLISIS INTELIGENTE DE PORTAFOLIO')
    st.caption('Análisis descriptivo de tus posiciones manuales. No conecta brokers ni ejecuta operaciones. Los cálculos no predicen rentabilidad.')
    if st.button('Consultar / actualizar análisis inteligente'):
        company_data.clear()
        st.session_state['intelligence_active']=True
    if not st.session_state.get('intelligence_active'):
        st.info('Pulsa consultar para obtener sectores, historial y dividendos de Yahoo Finance.')
        return
    histories, sectors, dividends, timestamps = {}, {}, {}, {}
    for symbol in positions:
        try:
            histories[symbol], sectors[symbol], dividends[symbol], timestamps[symbol]=company_data(symbol)
        except Exception:
            st.warning(f'{symbol}: historial, sector y dividendos no disponibles.')
    st.dataframe(pd.DataFrame([{'Ticker':symbol,'Sector':sectors.get(symbol) or 'No disponible','Consulta UTC':timestamps.get(symbol,'No disponible')} for symbol in positions]),width='stretch')
    if set(quotes)!=set(positions):
        st.warning('Faltan precios: no se calculan pesos completos, riesgo, rebalanceo ni puntuación. Las posiciones originales se conservan.')
        return
    values={symbol:float(item['acciones'])*quotes[symbol] for symbol,item in positions.items()}
    w=weights(values)
    threshold=st.selectbox('Alerta de concentración por empresa (%)',[15,20,25],index=1)
    st.subheader('Diversificación')
    table=pd.DataFrame({'Empresa':w.index,'Peso (%)':w.values*100,'Sector':[sectors.get(symbol) or 'No disponible' for symbol in w.index]})
    st.dataframe(table,width='stretch')
    for symbol, weight in w.items():
        if weight*100>threshold:
            st.warning(f'{symbol}: {weight:.2%} supera el umbral {threshold} %.')
    grouped=table.groupby('Sector')['Peso (%)'].sum()
    st.dataframe(grouped.rename('Exposición sectorial (%)'),width='stretch')
    for sector, group in table.groupby('Sector'):
        if sector!='No disponible' and len(group)>1:
            st.info(f'Exposición compartida a {sector}: '+', '.join(group['Empresa']))
    st.caption('Los sectores ausentes se agrupan como No disponible, no como un sector conocido. Los porcentajes se basan en el valor actual, no en el costo.')
    risk=None
    st.subheader('Riesgo histórico')
    if set(histories)==set(positions):
        try:
            risk=historical_risk(histories,w)
            a,b=st.columns(2)
            a.metric('Volatilidad anualizada',f'{risk["volatility"]:.2%}')
            b.metric('Máxima caída histórica',f'{risk["drawdown"]:.2%}')
            st.caption(f'Período común: {risk["start"]:%d/%m/%Y} a {risk["end"]:%d/%m/%Y}; {risk["observations"]} rendimientos diarios. Cartera retrospectiva con pesos actuales constantes, rebalanceo diario teórico, 252 sesiones/año y cierres ajustados. No es el historial real de tu cuenta.')
            st.dataframe(risk['correlation'].style.format('{:.2f}',na_rep='No disponible'),width='stretch')
            figure=go.Figure(go.Scatter(x=risk['curve'].index,y=risk['curve'],name='Cartera retrospectiva normalizada'))
            figure.update_layout(template='plotly_dark',paper_bgcolor='#0C1424',plot_bgcolor='#172238',font_color='#E2E8F0')
            st.plotly_chart(figure,use_container_width=True,theme=None)
        except ValueError as error:
            st.warning(str(error))
    else:
        st.warning('Riesgo histórico no disponible: faltan historiales. No se excluyen posiciones para aparentar un análisis completo.')
    st.info('La volatilidad describe cuánto variaron los rendimientos; no mide todas las pérdidas posibles. La correlación va de −1 a 1: valores altos indican movimientos parecidos. La máxima caída es el retroceso desde un máximo anterior en la cartera retrospectiva.')
    total=sum(values.values())
    st.dataframe(pd.DataFrame([{'Caída HIPOTÉTICA (%)':drop,'Valor posterior (USD)':total*(1-drop/100),'Pérdida (USD)':total*drop/100} for drop in (10,20,30)]),width='stretch')
    st.caption('Choques simultáneos uniformes, sin probabilidades ni predicción. No representan el máximo riesgo posible.')
    st.subheader('Dividendos estimados')
    rows=[]
    for symbol,item in positions.items():
        estimate=dividend_estimate(float(item['acciones']),float(item['precio_promedio']),quotes[symbol],dividends.get(symbol))
        rows.append({'Ticker':symbol,**(estimate or {key:np.nan for key in ('Anual estimado (USD)','Promedio mensual (USD)','Yield (%)','Yield on cost (%)')})})
    dividend_table=pd.DataFrame(rows)
    st.dataframe(dividend_table.style.format({column:'{:,.2f}' for column in dividend_table.columns if column!='Ticker'},na_rep='No disponible'),width='stretch')
    known=dividend_table['Anual estimado (USD)'].dropna()
    if not known.empty:
        st.write(f'Ingreso anual estimado disponible: US$ {known.sum():,.2f} · promedio mensual: US$ {known.sum()/12:,.2f}'+(' · TOTAL PARCIAL' if len(known)<len(rows) else ''))
    st.warning('Dividendos variables y no garantizados. Se usa dividendRate anual por acción reportado por Yahoo; un campo ausente no equivale a cero. El promedio mensual es anual/12, no un calendario de pagos. No incluye retenciones ni efectos de divisa.')
    st.subheader('Rebalanceo solo con nuevas aportaciones')
    cash=st.number_input('Aportación adicional hipotética (USD)',min_value=0.,value=0.,step=100.)
    method=st.radio('Alternativa matemática',['Reparto proporcional (mantiene pesos)','Priorizar posiciones menores (reduce concentración)'])
    if method.startswith('Priorizar'):
        proposed=allocation(values,cash)
    else:
        proposed=pd.DataFrame({'Valor actual (USD)':pd.Series(values),'Aportación hipotética (USD)':w*cash,'Peso actual (%)':w*100,'Peso posterior (%)':w*100})
    st.dataframe(proposed.style.format('{:,.2f}'),width='stretch')
    required=max(0.,max(values.values())/(threshold/100)-total)
    st.caption(f'Para llevar la posición actualmente mayor hasta {threshold} % sin aportarle y sin vender, se requiere al menos US$ {required:,.2f} adicionales destinados al resto. Esta cifra no garantiza que ninguna otra posición supere el umbral.')
    st.info('Son repartos matemáticos entre las posiciones existentes, no selecciones de empresas ni recomendaciones de compra. No se consideran comisiones, impuestos ni cambios de precio. Si solo hay una posición, aportar no reduce su peso.')
    st.subheader('Puntuación transparente · 0 a 100')
    names=['Concentración por empresa','Concentración sectorial','Volatilidad','Máxima caída']
    limits=[]; importance=[]
    with st.expander('Configurar criterios y pesos'):
        for name,default in zip(names,(20.,35.,25.,30.)):
            limits.append(st.number_input(f'Referencia de {name} (%)',min_value=1.,value=default,max_value=100.)/100)
            importance.append(st.number_input(f'Peso de {name}',min_value=0.,value=1.,max_value=100.))
    if risk is None or any(not sectors.get(symbol) for symbol in positions):
        st.warning('Puntuación no disponible: requiere riesgo histórico y todos los sectores. No se inventan criterios ausentes.')
    elif sum(importance)==0:
        st.warning('Al menos un criterio debe tener peso positivo.')
    else:
        number,components=score(float(w.max()),float(grouped.max()/100),risk['volatility'],risk['drawdown'],limits,importance)
        st.metric('Puntuación descriptiva',f'{number:.1f} / 100')
        st.dataframe(pd.DataFrame({'Factor':names,'Puntos':components,'Peso':importance}),width='stretch')
    st.caption('Cada factor = 100 × máximo(0, 1 − valor/(2 × referencia)); la puntuación es la media ponderada. Menor concentración, volatilidad y caída aumentan los puntos. El umbral de referencia da 50 puntos y el doble da 0. Es una regla educativa configurable, no un modelo de rentabilidad, asesoramiento ni garantía de seguridad.')
