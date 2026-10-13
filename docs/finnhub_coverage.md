# Cobertura y plan Finnhub gratuito

## Evidencia disponible antes de implementar

| Ticker | Company Profile v2 | Key Metrics | Valores/unidades/períodos |
|---|---|---|---|
| MSFT | HTTP 200 comunicado por el usuario | HTTP 200 comunicado por el usuario | Pendiente de validar con respuesta real |
| META | No comprobado en vivo | No comprobado en vivo | Pendiente |
| HD | No comprobado en vivo | No comprobado en vivo | Pendiente |
| SOFI | No comprobado en vivo | No comprobado en vivo | Pendiente |
| INTU | No comprobado en vivo | No comprobado en vivo | Pendiente |

El usuario confirmó industria, capitalización y acciones en circulación en el perfil MSFT; no un campo sector. El diagnóstico previo observó nombres de métricas, no valores, unidades o fechas. No hay clave disponible en este entorno para afirmar cobertura autenticada. El plan gratuito anunciado por el usuario admite los dos endpoints y 60 consultas/minuto; esto no prueba el permiso para otros endpoints.

## Plan

Proveedor modular con lista cerrada `/stock/profile2` y `/stock/metric?metric=all`. Clave solo desde entorno o st.secrets. Consultas opcionales y caché por endpoint; límite compartido conservador de 50/minuto por proceso; pausa en 429, recuperación acotada de conexión/5xx, errores sanitizados. Solo esos dos endpoints se pueden invocar.

UI independiente de validación dentro de MI PORTAFOLIO. Para cada ticker de las cinco empresas, clasificar campos presentes, vacíos/inválidos y ausentes. Mostrar nombre original, valor del proveedor, período explícito en el nombre y unidad pendiente; no derivar fórmulas ni usar estos datos en puntuación/dividendos/cálculos actuales hasta validarlos. No inventar un forward P/E o ROIC de campos parecidos.

TLT y BTCI se excluyen del análisis de empresas. Se mantienen CSV, posiciones, cálculos técnicos/históricos, sectores Yahoo y manuales de distribuciones. Industria Finnhub nunca se asigna al sector Yahoo. Se informa de fecha de consulta frente a fecha económica (no siempre suministrada). No hay DCF ni endpoints de dividendos, estimaciones o estados financieros adicionales.

## Puerta de validación posterior

Activar la clave en Streamlit y consultar cada uno de los cinco tickers. Revisar nombres exactos, período (annual, quarterly, TTM o forward), unidades, base contable y fecha contra documentación y estados oficiales. Registrar campos que realmente aparecen sin asumir nombres candidatos. La extracción en esta entrega es descriptiva y pendiente de validación económica; no declara como fiables métricas por su mera presencia.
