from copy import deepcopy
from datetime import date
import json
import pandas as pd
import streamlit as st
from distributions import DEFAULTS, validate_record, load_manual, distribution_result


def render_distributions(positions, quotes, yahoo):
    st.subheader('Distribuciones TTM y dividendos')
    st.caption('Datos manuales aportados por el usuario con fuente declarada; no se verifican automáticamente ni se consulta una cuenta de Interactive Brokers.')
    records=st.session_state.setdefault('manual_distributions',deepcopy(DEFAULTS))
    with st.expander('Actualizar datos manuales sin editar código'):
        st.caption('La fecha inicial 13/10/2026 es la fecha de incorporación de los datos facilitados por el usuario, no una comprobación independiente con Interactive Brokers. Los cambios se guardan en esta sesión; exporta tu copia JSON para conservarlos.')
        symbol=st.selectbox('ETF para actualizar',list(records),key='manual_etf')
        current=records[symbol]
        with st.form(f'distributions_{symbol}'):
            annual=st.number_input('Distribución anual TTM por acción (USD)',min_value=0.,value=float(current['annual']),format='%.4f')
            reported=st.number_input('Yield TTM reportado (%)',min_value=0.,value=float(current.get('reported_yield') or 0.))
            source=st.text_input('Fuente del dato manual',value=current['source'])
            updated=st.date_input('Fecha de actualización del dato manual',value=date.fromisoformat(current['updated']))
            frequency=st.text_input('Frecuencia habitual',value=current.get('frequency','No especificada'))
            confirmed=st.checkbox('Incluir distribución confirmada',value=current.get('payment') is not None)
            payment=st.number_input('Distribución confirmada por acción (USD)',min_value=0.,value=float(current.get('payment') or 0.),format='%.4f')
            ex=st.date_input('Fecha ex-dividendo',value=date.fromisoformat(current['ex_date']) if current.get('ex_date') else date.today())
            pay=st.date_input('Fecha de pago',value=date.fromisoformat(current['pay_date']) if current.get('pay_date') else date.today())
            save=st.form_submit_button('Guardar datos de distribuciones')
        if save:
            try:
                records[symbol]=validate_record({'annual':annual,'reported_yield':reported,'source':source,'updated':updated.isoformat(),'frequency':frequency,'payment':payment if confirmed else None,'ex_date':ex.isoformat() if confirmed else None,'pay_date':pay.isoformat() if confirmed else None})
                st.success('Datos actualizados; las posiciones no se han modificado.')
            except ValueError as error: st.error(str(error))
        uploaded=st.file_uploader('Restaurar copia de distribuciones JSON',type=['json'])
        if st.button('Importar datos de distribuciones'):
            try:
                if uploaded is None: raise ValueError('Selecciona primero una copia JSON.')
                incoming=load_manual(uploaded.getvalue())
                records.update(incoming)
                st.rerun()
            except ValueError as error: st.error(str(error))
        st.download_button('Exportar datos de distribuciones JSON',json.dumps(records,ensure_ascii=False,indent=2),file_name='mis_distribuciones.json',mime='application/json')
    rows=[]; payments=[]
    for symbol,item in positions.items():
        result=distribution_result(item['acciones'],item['precio_promedio'],quotes.get(symbol),records.get(symbol),yahoo.get(symbol))
        rows.append({'Ticker':symbol,**(result or {'Base':yahoo.get(symbol,{}).get('basis','No disponible') if isinstance(yahoo.get(symbol),dict) else 'No disponible'})})
        manual=records.get(symbol)
        if manual:
            try: manual=validate_record(manual)
            except ValueError: manual=None
        if manual and manual.get('payment') is not None:
            payments.append({'Ticker':symbol,'Distribución confirmada por acción (USD)':manual['payment'],'Ex-dividendo':manual['ex_date'],'Fecha de pago':manual['pay_date'],'Fuente':manual['source'],'Actualización':manual['updated']})
    table=pd.DataFrame(rows)
    for column in ('Yield TTM reportado (%)','Actualización manual','Frecuencia habitual'):
        if column in table:
            table[column]=table[column].map(lambda value: 'No disponible / no aplica' if pd.isna(value) else (f'{value:.4f}' if column == 'Yield TTM reportado (%)' else str(value)))
    numeric=table.select_dtypes('number').columns
    st.dataframe(table.style.format({key:'{:,.4f}' for key in numeric},na_rep='No disponible'),width='stretch')
    if 'Ingreso anual de referencia (USD)' in table:
        known=table['Ingreso anual de referencia (USD)'].dropna()
        if len(known):
            st.write(f'Ingreso anual de referencia: US$ {known.sum():,.2f} · promedio mensual: US$ {known.sum()/12:,.2f}'+(' · TOTAL PARCIAL' if len(known)<len(rows) else ''))
    st.caption('Las tasas automáticas incluyen el campo de Yahoo utilizado. Si dividendRate falta, se utiliza trailingAnnualDividendRate solo si es válido, identificado como TTM reportado por Yahoo, no verificado independientemente. No se deriva un dividendo de porcentajes ni de precios.')
    st.caption('Los registros manuales válidos tienen prioridad para TTM. El yield reportado corresponde al dato aportado y no se recalcula: puede diferir del yield al último cierre. Yield on cost = distribución anual por acción / costo promedio. Yahoo dividendRate no se etiqueta como TTM histórico confirmado.')
    st.markdown('**Distribuciones confirmadas · separadas del promedio TTM**')
    if payments: st.dataframe(pd.DataFrame(payments),width='stretch')
    else: st.info('No hay pagos confirmados registrados para estas posiciones.')
    st.warning('El promedio mensual histórico es anual/12, no una promesa ni un calendario de pagos. Las distribuciones futuras son variables y no están garantizadas. Un pago confirmado por acción no acredita un cobro personal: depende de las acciones con derecho al pago en la fecha correspondiente. No se suman los pagos confirmados al TTM, para evitar doble conteo. Sin impuestos ni retenciones.')
