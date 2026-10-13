import os
import pandas as pd
import streamlit as st
from finnhub_provider import FinnhubProvider,Budget,metric_rows
from fundamental_data import normalize_finnhub,series_rows

COMPANIES=('MSFT','META','HD','SOFI','INTU')

@st.cache_resource
def _budget():return Budget()


def _key():
 value=os.environ.get('FINNHUB_API_KEY')
 if value:return value
 try:return st.secrets.get('FINNHUB_API_KEY')
 except Exception:return None


def render_finnhub(positions):
 st.header('Finnhub gratuito · validación de fundamentales')
 st.caption('Solo Company Profile v2 y Key Metrics. No consulta dividendos históricos, estimaciones adicionales ni endpoints de pago. Yahoo, posiciones y manuales permanecen independientes.')
 if not _key():
  st.info('Configura FINNHUB_API_KEY en variables de entorno o Secrets de Streamlit. No pegues la clave en el portafolio ni en el CSV.')
  return
 st.warning('La presencia de un campo no verifica sus unidades, fecha económica o significado. Estos valores no se utilizan aún en dividendos, puntuación, valoración ni DCF.')
 if not st.checkbox('Activar consultas Finnhub para esta sesión',key='finnhub_enabled'):return
 if 'finnhub_provider' not in st.session_state:
  st.session_state['finnhub_provider']=FinnhubProvider(_key(),budget=_budget())
 provider=st.session_state['finnhub_provider']
 if st.button('Actualizar datos Finnhub'):provider.refresh()
 symbols=[symbol for symbol in positions if symbol in COMPANIES]
 excluded=[symbol for symbol in positions if symbol not in COMPANIES]
 if excluded:st.info('Sin análisis empresarial en esta fase: '+', '.join(excluded)+'. BTCI/TLT conservan su tratamiento ETF y datos manuales.')
 for symbol in symbols:
  st.subheader(symbol+' · Finnhub')
  profile_currency=None
  for endpoint,title in [('profile','Company Profile v2'),('metrics','Key Metrics')]:
   result=provider.get(symbol,endpoint)
   st.caption(f'{title} · fuente Finnhub · consulta UTC: {result.fetched_at or "No disponible"} · último intento UTC: {result.checked_at}. Fecha económica no confirmada por esta consulta.')
   if result.error:st.warning(f'{symbol} · {title}: {result.error} · HTTP {result.status or "no disponible"}'+(' · DESACTUALIZADO: último dato válido' if result.stale else ''))
   if result.data is None:continue
   if endpoint=='profile':
    supplied_currency=result.data.get('currency')
    profile_currency=supplied_currency if isinstance(supplied_currency,str) and len(supplied_currency)==3 and supplied_currency.isupper() else None
    rows=[{'Campo':field,'Valor del proveedor':str(value) if value is not None else 'No disponible','Fuente':'Finnhub'} for field,value in result.data.items()]
    if rows:st.dataframe(pd.DataFrame(rows),width='stretch')
    else:st.info('Perfil sin campos disponibles.')
    st.caption('finnhubIndustry es industria, no sector GICS. Capitalización y acciones se muestran en la escala original; unidades y moneda requieren contraste antes de utilizarlas en cálculos.')
   else:
    normalized=normalize_finnhub(result.data,result.fetched_at,currency=profile_currency,stale=result.stale)
    st.markdown('**Capa normalizada · contratos pendientes de validación**')
    normalized_table=pd.DataFrame(normalized).rename(columns={'indicator':'Indicador','raw_value':'Valor original','normalized_value':'Valor normalizado','period_kind':'Período','economic_date':'Fecha económica','fetched_at':'Consulta UTC','status':'Estado','proposed_source_unit':'Unidad candidata'})
    st.dataframe(normalized_table[['Indicador','field','Valor original','Valor normalizado','Unidad candidata','Período','Fecha económica','Consulta UTC','Estado']].style.format({'Valor original':'{:,.4f}','Valor normalizado':'{:,.4f}'},na_rep='No disponible'),width='stretch')
    fiscal=series_rows(result.data,result.fetched_at,result.stale)
    if fiscal:
     with st.expander('Series fiscales reportadas · fechas distintas de la consulta'):
      st.dataframe(pd.DataFrame(fiscal),width='stretch')
    st.caption('Los porcentajes se convertirán a fracción solo con un contrato de unidad validado (25 % → 0.25). No se asume la escala por el tamaño del número. Ningún dato se declara listo para precio justo; TTM no implica una fecha fiscal conocida.')
    st.dataframe(pd.DataFrame(metric_rows(result.data)).style.format({'Valor proveedor':'{:,.4f}'},na_rep='No disponible'),width='stretch')
    with st.expander('Todos los campos numéricos devueltos · sin interpretación automática'):
     st.dataframe(pd.DataFrame([{'Campo':field,'Valor original':value} for field,value in result.data.items() if field != '__series__']),width='stretch')
    st.caption('No devuelto con este nombre puede tener un equivalente con otra denominación. No se deduce Forward P/E, ROIC, flujo libre ni dividendos de otros campos. TTM, anual y trimestral se mantienen separados.')
