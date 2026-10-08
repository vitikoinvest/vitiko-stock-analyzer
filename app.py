from datetime import datetime, timezone
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from analysis import indicators, trend, levels
from data import demo_prices, load_prices, validate_ticker

st.set_page_config(page_title='VITICO STOCK ANALYZER', page_icon='📈', layout='wide')
st.markdown("""<style>
.stApp {background: #0C1424; color: #E2E8F0; color-scheme: dark;}
h1, h2, h3 {color: #FFFFFF;}
[data-testid="stCaptionContainer"], [data-testid="stMetricLabel"],
[data-testid="stMarkdownContainer"], label {color: #E2E8F0;}
[data-testid="stSidebar"] {background: #111D32; color: #E2E8F0;}
[data-testid="stMetric"] {background: #172238; padding: 18px;
    border: 1px solid #64748B; border-radius: 12px; height: 100%;}
[data-testid="stMetricValue"] {color: #FFFFFF;}
[data-testid="stMetricValue"] > div {white-space: normal; overflow-wrap: anywhere;
    font-size: clamp(1.25rem, 2.5vw, 2rem);}
[data-testid="stAlert"] {background: #172238; border: 1px solid #64748B; color: #E2E8F0;}
[data-testid="stAlert"] p {color: #E2E8F0;}
[data-testid="stExpander"] {background: #172238; border-color: #64748B;}
.stTextInput input {color: #FFFFFF; background: #172238;}
.stTextInput input::placeholder {color: #E2E8F0; opacity: 1;}
[data-baseweb="select"] > div {color: #FFFFFF; background: #172238; border-color: #64748B;}
.stButton button, .stFormSubmitButton button {background: #4ADE80;
    color: #0C1424; border: 1px solid #4ADE80; min-height: 44px; font-weight: 600;}
.stButton button p, .stFormSubmitButton button p {color: #0C1424;}
.stButton button:hover, .stFormSubmitButton button:hover {background: #86EFAC;
    color: #0C1424; border-color: #FFFFFF;}
button:focus-visible, input:focus-visible {outline: 3px solid #FFFFFF; outline-offset: 3px;}
a {color: #93C5FD; text-decoration: underline;}
@media (max-width: 640px) {
    [data-testid="stMetric"] {padding: 12px;}
    [data-testid="stMetricValue"] > div {font-size: 1.5rem;}
    h1 {font-size: 1.8rem; overflow-wrap: anywhere;}
}
</style>""", unsafe_allow_html=True)
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
trend_color = '#4ADE80' if label == 'Alcista' else '#F87171' if label == 'Bajista' else '#E2E8F0'
st.markdown(
    f'<p style="color:{trend_color};font-weight:600">Tendencia: {label}</p>',
    unsafe_allow_html=True,
)
st.info(explanation)
years = {'1 año': 1, '2 años': 2, '5 años': 5}[period]
visible = data.loc[data.index >= data.index[-1] - pd.DateOffset(years=years)]
support, resistance = levels(data)
fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.06, row_heights=[.6,.2,.2], subplot_titles=('Precio y medias móviles · USD', 'RSI · 14 sesiones', 'MACD · 12, 26, 9'))
for name, title, color in [('Close','Cierre','#FFFFFF'),('SMA50','Media 50','#4ADE80'),('SMA100','Media 100','#fbbf24'),('SMA200','Media 200','#c084fc')]:
    fig.add_trace(go.Scatter(x=visible.index, y=visible[name], name=title, line=dict(color=color, width=2)), row=1, col=1)
fig.add_hline(y=support, line_dash='dot', line_color='#4ADE80', row=1, col=1)
fig.add_hline(y=resistance, line_dash='dot', line_color='#f87171', row=1, col=1)
fig.add_trace(go.Scatter(x=visible.index,y=visible['RSI'],name='RSI',line_color='#fbbf24'),row=2,col=1)
for threshold in (30,70):
    fig.add_hline(y=threshold,line_dash='dot',line_color='#E2E8F0',row=2,col=1)
fig.update_yaxes(range=[0,100],row=2,col=1)
for name, title, color in [('MACD','MACD','#93C5FD'),('Signal','Señal','#FBBF24')]:
    fig.add_trace(go.Scatter(x=visible.index,y=visible[name],name=title,line=dict(color=color, width=2)),row=3,col=1)
fig.add_trace(go.Bar(x=visible.index,y=visible['Histogram'],name='Histograma',marker_color=['#4ADE80' if value >= 0 else '#F87171' for value in visible['Histogram']]),row=3,col=1)
fig.update_layout(template='plotly_dark',height=780, paper_bgcolor='#0c1424',plot_bgcolor='#172238',font=dict(color='#E2E8F0', size=13), legend=dict(orientation='h', y=-.12, x=0, font=dict(color='#E2E8F0'), bgcolor='#0C1424'), hoverlabel=dict(bgcolor='#172238', font_color='#FFFFFF'), margin=dict(l=45,r=15,t=60,b=120))
fig.update_xaxes(tickfont=dict(color='#E2E8F0'), gridcolor='#334155', linecolor='#64748B', automargin=True)
fig.update_yaxes(tickfont=dict(color='#E2E8F0'), gridcolor='#334155', zerolinecolor='#64748B', automargin=True)
fig.update_annotations(font=dict(color='#FFFFFF', size=14))
st.plotly_chart(fig, use_container_width=True, theme=None)
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
