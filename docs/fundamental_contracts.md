# Capa de fundamentales normalizados: estado de validación

## Acceso al plan frente a cobertura de un indicador

Company Profile v2 y Key Metrics responden para MSFT/META/HD/SOFI según comprobación del usuario en Streamlit Cloud. INTU sigue pendiente de confirmación real en este entorno. Ninguna clave disponible aquí; no se han descargado sus valores para contrastar. Documentación oficial https://finnhub.io/docs/api/company-basic-financials bloqueada por proxy 403 en esta ejecución.

Acceso HTTP 200 al endpoint no prueba la presencia ni significado de cada indicador. Un campo ausente no demuestra que sea de pago. No se consultan endpoints nuevos. Las denominaciones siguientes son contratos candidatos explícitos; no se valida una fórmula por el tamaño del número.

| Indicador | Campo candidato | Unidad propuesta | Período propuesto | Comprobación pendiente |
|---|---|---|---|---|
| P/E | peTTM | múltiplo | TTM | EPS utilizado, tratamiento de pérdidas/ajustes |
| Forward P/E | forwardPE | múltiplo | futuro | Campo real, horizonte y consenso; no derivar |
| PEG | pegTTM | ratio | TTM | Ventana de crecimiento y escala; no derivar |
| EPS | epsTTM / epsAnnual | moneda por acción | TTM / anual | Moneda, básico/diluido, extraordinarios y ejercicio |
| ROE / ROA | roeTTM / roaTTM | puntos porcentuales | TTM | Denominador medio o final |
| Márgenes | grossMarginTTM / operatingMarginTTM / netProfitMarginTTM | puntos porcentuales | TTM | Ajustes contables y numerador |
| Dividend yield | currentDividendYieldTTM | puntos porcentuales | TTM | Ventana de dividendos y precio de referencia |
| Payout | payoutRatioAnnual | puntos porcentuales | anual | Beneficios/base de dividendos utilizada |

Estos campos no se sustituyen por aliases parecidos. Se conservan todos los campos originales en la vista de inspección para revisar denominaciones diferentes sin asumir equivalencia. Capitalización, flujo libre, ROIC, deuda y otros candidatos del panel anterior siguen pendientes de contratos; no se utilizan en valoración. Industria no equivale a sector.

## Normalización

`fundamental_data.normalize_finnhub` conserva raw_value, fuente Finnhub, endpoint, campo, moneda explícita cuando el perfil la proporciona, fecha de consulta y estado de antigüedad. `normalized_value` permanece vacío hasta recibir un contrato por campo con unidad/período coincidentes, definición y referencia de validación. La aplicación no introduce aprobaciones ficticias: por defecto todas están pendientes.

Los contratos aprobados se pasarían desde una configuración auditada en una fase posterior; no hay un botón que marque arbitrariamente todos los datos como fiables. Las pruebas usan aprobaciones simuladas, que no constituyen evidencia de datos reales. Una moneda ausente bloquea la aprobación de importes por acción. Porcentajes confirmados en puntos porcentuales se dividen entre 100; ratios/múltiplos e importes no se escalan. Se conservan negativos y cero explícito; None, booleanos, infinitos y strings no se convierten a cero. Valores anómalos deben revisarse, no truncarse artificialmente a 0–100 %.

## Fechas

Snapshots `metric` no tienen fecha económica confirmada: `economic_date=None`, aunque el nombre incluya TTM/Annual. La fecha de consulta no se usa como cierre fiscal ni publicación. Se preservan series `series.annual/quarterly` con sus pares period/v en un espacio separado: fecha de período reportada, no fecha de publicación ni fecha atribuida a snapshots. Sus unidades/definiciones no se infieren del período. Se retienen hasta 100 observaciones por campo de cada respuesta para acotar memoria.

## Pendiente antes de precio justo

Obtener las respuestas reales de los cinco tickers y contrastar los campos con documentación accesible y estados oficiales, conservando referencia de cada contrato, unidades, ajustes y fecha aplicable. Identificar qué EPS corresponde al P/E. Confirmar datos de flujo de caja, deuda, capital, dilución, crecimiento y supuestos necesarios antes de seleccionar un método de valoración. Forward P/E/PEG no se consideran disponibles por el mero acceso al endpoint. No se usan servicios de pago ni endpoints no autorizados.

`valuation_ready=False` en esta entrega incluso con contrato de prueba: no hay garantía de suficiencia para valoración. No se implementa DCF ni precio justo. Finnhub, Yahoo y las distribuciones TTM manuales permanecen separados. No se modifican posiciones ni cálculos previos.
