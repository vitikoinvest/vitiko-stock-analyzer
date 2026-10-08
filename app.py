from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from analysis import indicators, trend, levels
from data import demo_prices, load_prices, validate_ticker

st.set_page_config(page_title='VITICO STOCK ANALYZER', page_icon='📈', layout='wide')
st.markdown('''<style>.stApp {background: #0c1424; color: #e6edf7;} h1,h2,h3 {color: #e6edf7;} [data-testid="stMetric"] {background: #172238; padding: 18px; border-radius: 12px;} </style>''', unsafe_allow_html=True)
st.title('VITICO STOCK ANALYZER')
st.caption('Una perspectiva clara para invertir a largo plazo · Análisis técnico')
with st.sidebar:
    st.header('Tu análisis')
    mode = st.radio('Origen de los datos', ['Datos reales · Yahoo Finance', 'Demostración · datos simulados'])
    with st.form('search'):
        ticker = st.text_input('Ticker de una acción estadounidense', 'MSFT', help='Ejemplos: AMZN, MSFT, UPS, META, BRK-B')
        st.form_submit_button('Analizar', use_container_width=True)
    period = st.selectbox('Período visible', ['1 año', '2 años', '5 años'])
    refresh = st.button('Actualizar datos', use_container_width=True)
    st.caption('No se conectan cuentas ni se realizan compras o ventas.')

@st.cache_data(ttl=900, show_spinner=False)
def fetch(symbol):
    return load_prices(symbol), datetime.now(timezone.utc)

if refresh:
    fetch.clear()
try:
    symbol = validate_ticker(ticker)
    demo = mode.startswith('Demostración')
    with st.spinner('Preparando el análisis…'):
        if demo:
            prices, fetched = demo_prices(), None
        else:
            prices, fetched = fetch(symbol)
    data = indicators(prices)
except Exception:
    st.error('No se pudo obtener el historial. Comprueba el ticker y la conexión, o vuelve a intentarlo más tarde. No se han generado precios ni indicadores de sustitución.')
    st.info('Puedes seleccionar «Demostración» para explorar la interfaz con datos simulados.')
    st.stop()

if demo:
    st.warning('DEMOSTRACIÓN — Precios sintéticos reproducibles. No representan ninguna acción ni sirven para tomar decisiones de inversión.')
    st.subheader('Ejemplo educativo · DEMO')
else:
    st.subheader(f'{symbol} · Datos reales de Yahoo Finance')
    st.caption(f'Consulta realizada: {fetched:%d/%m/%Y %H:%M} UTC · Caché de hasta 15 minutos.')
st.caption(f'Última sesión disponible: {data.index[-1]:%d/%m/%Y} · Precios de cierre ajustados, en USD. Las fechas corresponden al índice de la fuente; no son cotizaciones en tiempo real.')
last = data.iloc[-1]
label, explanation = trend(data)
cols = st.columns(4)
cols[0].metric('Último cierre ajustado', f"US$ {last['Close']:,.2f}")
cols[1].metric('Tendencia estimada', label)
cols[2].metric('RSI · 14 sesiones', 'No disponible' if pd.isna(last['RSI']) else f"{last['RSI']:.1f}")
cols[3].metric('Sesiones disponibles', str(len(data)))
st.info(explanation)
years = {'1 año': 1, '2 años': 2, '5 años': 5}[period]
visible = data.loc[data.index >= data.index[-1] - pd.DateOffset(years=years)]
support, resistance = levels(data)
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.06, row_heights=[.6,.2,.2], subplot_titles=('Precio y medias móviles · USD', 'RSI · 14 sesiones', 'MACD · 12, 26, 9'))
for name, title, color in [('Close','Cierre','#60a5fa'),('SMA50','Media 50','#34d399'),('SMA100','Media 100','#fbbf24'),('SMA200','Media 200','#c084fc')]:
    fig.add_trace(go.Scatter(x=visible.index, y=visible[name], name=title, line=dict(color=color)), row=1, col=1)
fig.add_hline(y=support, line_dash='dot', line_color='#34d399', row=1, col=1)
fig.add_hline(y=resistance, line_dash='dot', line_color='#f87171', row=1, col=1)
fig.add_trace(go.Scatter(x=visible.index,y=visible['RSI'],name='RSI',line_color='#fbbf24'),row=2,col=1)
for threshold in (30,70):
    fig.add_hline(y=threshold,line_dash='dot',row=2,col=1)
fig.update_yaxes(range=[0,100],row=2,col=1)
for name, title in [('MACD','MACD'),('Signal','Señal')]:
    fig.add_trace(go.Scatter(x=visible.index,y=visible[name],name=title),row=3,col=1)
fig.add_trace(go.Bar(x=visible.index,y=visible['Histogram'],name='Histograma'),row=3,col=1)
fig.update_layout(template='plotly_dark',height=780, paper_bgcolor='#0c1424',plot_bgcolor='#172238',legend=dict(orientation='h'),margin=dict(l=20,r=20,t=40,b=20))
st.plotly_chart(fig, use_container_width=True)
a,b = st.columns(2)
a.metric('Soporte estimado · 60 sesiones', f'US$ {support:,.2f}')
b.metric('Resistencia estimada · 60 sesiones', f'US$ {resistance:,.2f}')
st.caption('Estimación sencilla: mínimo y máximo de los cierres de las últimas 60 sesiones disponibles. Son referencias aproximadas, no barreras garantizadas; no usan máximos y mínimos intradía.')
with st.expander('Cómo interpretar los indicadores', expanded=True):
    st.markdown('''- **Medias móviles:** precio medio de las últimas 50, 100 y 200 sesiones bursátiles, no días naturales. Ayudan a ver la dirección general.
- **RSI:** mide la fuerza de los movimientos recientes. Por encima de 70 puede indicar un movimiento intenso al alza; por debajo de 30, una caída intensa. No equivale a una orden de vender o comprar.
- **MACD:** compara medias exponenciales de 12 y 26 sesiones; su señal utiliza 9 períodos. Los cruces ayudan a observar cambios de impulso, pero pueden dar falsas señales.
- **Tendencia:** regla orientativa que compara cierre, medias de 50 y 200 sesiones y la variación de la media de 200 en 20 sesiones (umbral de ±0,5 %). Las señales mixtas se agrupan como lateral.
- Si faltan sesiones, los indicadores correspondientes aparecen como **no disponibles**.''')
with st.expander('Fuente y limitaciones'):
    st.markdown('''Los datos reales proceden de **Yahoo Finance**, obtenidos con la biblioteca **yfinance**, un proyecto independiente sin relación oficial con Yahoo. Se solicitan cinco años de cierres diarios ajustados por eventos corporativos. Los ajustes pueden modificar el historial y no equivalen al precio de ejecución de una operación.

La fuente puede sufrir retrasos, errores, cambios de cobertura o límites de consultas. El ticker introducido debe corresponder a una acción estadounidense; esta versión no certifica mercado ni tipo de instrumento. Yahoo también admite otros instrumentos. La caché conserva consultas durante 15 minutos; «Actualizar datos» solicita una nueva consulta. Revisa la fecha de la última sesión para detectar datos antiguos. El modo demo siempre es explícito y nunca se activa automáticamente.

Esta herramienta es educativa. El análisis técnico no incluye valoración, dividendos ni situación financiera y no constituye una recomendación de inversión. Consulta los términos de Yahoo Finance antes de redistribuir datos.''')
