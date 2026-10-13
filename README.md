# VITICO STOCK ANALYZER

Aplicación educativa de análisis técnico para un inversor a largo plazo. Interfaz completamente en español, sin cuentas de bancos o brokers y sin operaciones de compra o venta.

## Cómo visualizarla

Necesitas Python 3.12 y conexión a Internet para descargar dependencias y consultar precios reales. Abre una terminal en esta carpeta y ejecuta:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

En Windows, activa el entorno con `.venv\Scripts\activate` en lugar de `source`. Streamlit muestra en la terminal la dirección que puedes abrir en el navegador de tu ordenador. Si utilizas una máquina remota, necesitas acceso al puerto 8501 mediante el sistema de tu proveedor; el entorno de onboarding no ofrece una vista web integrada.

1. Selecciona **Datos reales · Yahoo Finance**.
2. Escribe un ticker, por ejemplo MSFT, AMZN, UPS o META, y pulsa **Analizar**.
3. Comprueba la fecha de la última sesión disponible.
4. Explora el gráfico y sus medias. Cambia el período visible sin modificar los cinco años usados para calcular indicadores.
5. Lee la explicación de tendencia e indicadores debajo del gráfico.
6. Usa **Actualizar datos** para renovar la consulta; normalmente se guarda durante 15 minutos.

Si la fuente falla, se muestra un error y no se inventan datos. Puedes elegir explícitamente **Demostración** para explorar precios sintéticos reproducibles, sin relación con el ticker introducido. No uses la demo para decisiones financieras.

## Qué incluye

- Cierres diarios ajustados en USD, hasta cinco años de historial.
- Medias simples de 50, 100 y 200 sesiones.
- RSI de 14 sesiones con suavizado de Wilder; MACD exponencial de 12/26 sesiones y señal de 9.
- Soporte/resistencia aproximados: mínimo/máximo de los últimos 60 cierres disponibles.
- Tendencia orientativa basada en precio, medias de 50/200 y pendiente de la media de 200 durante 20 sesiones.

Los indicadores sin historial suficiente quedan sin valor. Las medias cuentan sesiones bursátiles, no días naturales. La clasificación lateral incluye señales mixtas y no confirma un mercado sin tendencia.

## Fuente y límites

Fuente identificada: [Yahoo Finance](https://finance.yahoo.com/), consultada con [yfinance](https://github.com/ranaroussi/yfinance), biblioteca independiente y no oficial. No requiere una clave para este uso. Puede haber límites, retrasos, errores o cambios de cobertura; no son datos en tiempo real garantizados. El historial ajustado puede cambiar tras dividendos o desdoblamientos. Esta versión acepta símbolos compatibles, pero no verifica que el instrumento sea una acción estadounidense ni certifica su moneda. Está diseñada para acciones estadounidenses cotizadas en USD.

Respeta los términos de la fuente, especialmente antes de redistribuir datos o usarla comercialmente. El análisis es educativo y no constituye asesoramiento. No incluye todavía análisis fundamental, valoración, dividendos ni seguimiento de inversores.

## Archivos

- `app.py`: interfaz, gráficos y gestión de consultas.
- `data.py`: consulta real, validación del ticker y demo explícita.
- `analysis.py`: indicadores, tendencia y niveles estimados.
- `requirements.txt`: versiones de las dependencias principales.
- `tests/`: comprobaciones de indicadores, demo y manejo de errores.
- `.gitignore`: excluye el entorno local, cachés y secretos.

## Pruebas

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Las pruebas usan series conocidas y simulan un error de la fuente; no necesitan acceso externo. Una consulta real depende de la disponibilidad de Yahoo Finance. Para ejecutar en una máquina remota:

```bash
.venv/bin/python -m streamlit run app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

## Estado de validación en el entorno cloud

Se instalaron las dependencias y se comprobó el arranque de Streamlit, su endpoint de salud y las pruebas automatizadas de cálculos e interfaz. La prueba real de MSFT devolvió `CONNECT tunnel failed, response 403`: el proxy de red bloquea Yahoo Finance. Este fue el resultado de la validación inicial. En la validación posterior del simulador la consulta real de MSFT funcionó, devolviendo 1255 sesiones; también se comprobó la interfaz con esa fuente real. La disponibilidad futura sigue dependiendo de Yahoo Finance y de la red.

Se guardó un borrador con instrucciones de instalación/arranque y acceso a `query1.finance.yahoo.com`, `query2.finance.yahoo.com`, `fc.yahoo.com`, `guce.yahoo.com` y `finance.yahoo.com`. Revisa y guarda esos cambios en los ajustes del entorno, y publica el entorno. Después hay que repetir la consulta real para confirmar el acceso; guardar un borrador no cambia la red de la máquina actual.

## SIMULADOR DE ESCENARIOS DE INVERSIÓN

El nuevo módulo está debajo del análisis histórico y conserva todas sus funciones. Compatible con Python 3.12 y Streamlit Community Cloud sin dependencias adicionales. Para desplegar en Community Cloud selecciona este repositorio, la rama que contenga los cambios, el archivo principal `app.py` y Python 3.12. `.streamlit/config.toml` mantiene el tema oscuro.

1. Selecciona **Datos reales · Yahoo Finance**, escribe el ticker y pulsa **Analizar**. El simulador utiliza el mismo historial disponible; si la fuente falla, no se genera una base real falsa. En modo demostración se etiqueta explícitamente toda la base como sintética.
2. Baja a **SIMULADOR DE ESCENARIOS DE INVERSIÓN**. El precio inicial predeterminado es el último cierre ajustado; puedes cambiarlo sin modificar el historial.
3. Elige 1, 3, 6 o 12 meses y los cambios porcentuales de los escenarios alcista, bajista y neutral. Se permiten subidas superiores al 100 %; las caídas deben ser menores del 100 % para mantener precios positivos.
4. Elige trayectoria lineal, compuesta o cambio tardío. Ajusta la oscilación para explorar caminos distintos con el mismo precio final.
5. Introduce entrada, stop-loss, objetivo y número de acciones. Para una posición compradora se exige `0 < stop < entrada < objetivo`. Se muestra la ganancia potencial, pérdida potencial y beneficio dividido entre riesgo. No se envía ninguna orden.
6. Compara precios e indicadores finales en la tabla y selecciona un escenario para explorar su RSI, MACD, Bollinger y medias.

**Supuestos explícitos:** trayectorias deterministas, sin probabilidades ni previsión estadística. Lineal interpola el precio; compuesta interpola su logaritmo; cambio tardío usa una interpolación cuadrática. La oscilación aplica dos ciclos sinusoidales a los logaritmos de los precios y conserva los extremos. Se usan días de lunes a viernes hasta la fecha del horizonte, sin excluir festivos de mercado. No se modelan comisiones, impuestos, dividendos, inflación ni saltos de ejecución. Un stop-loss no garantiza una pérdida máxima.

La observación inicial manual se añade un segundo después del último cierre real: representa un salto hipotético y cuenta como una observación adicional para los indicadores. No se sobrescribe ni reescala el historial. RSI, MACD y medias reutilizan los cálculos originales; Bollinger utiliza 20 observaciones y dos desviaciones estándar poblacionales. Sin historial suficiente, los valores no disponibles no se inventan. El histórico aparece con línea continua y el tramo simulado con línea discontinua, acompañado de etiquetas. Estas simulaciones no son predicciones ni recomendaciones.

## Mi inversión actual: acciones fraccionarias y costo promedio

En el simulador aparece **MI INVERSIÓN ACTUAL**. Introduce tu **Número de acciones** (mínimo 0.0001, hasta cuatro decimales) y **Mi precio promedio de compra (Average Price)**. Son datos manuales; no se conectan cuentas ni se conservan fuera de la sesión. MSFT propone un ejemplo editable de 9.42 acciones y US$ 372.42 de costo promedio, no una posición detectada.

- Capital invertido = cantidad × costo promedio.
- Valor actual = cantidad × último cierre ajustado disponible de Yahoo Finance.
- Resultado no realizado = valor actual − capital invertido.
- Rentabilidad = resultado / capital invertido × 100.
- Precio de equilibrio = costo promedio, excluyendo comisiones, impuestos y dividendos.

El ejemplo produce US$ 3,508.1964, mostrado como **US$ 3,508.20**. La pantalla usa punto decimal y coma de miles. Puedes cambiar cualquier valor. La demo utiliza precios sintéticos y se identifica expresamente; no representa el valor de una posición real.

La tabla añade **valor futuro hipotético**, resultado y rentabilidad respecto al costo promedio, y diferencia frente al valor actual. Conserva también la columna de resultado frente a la entrada para riesgo/beneficio. Cambiar la entrada o el precio inicial hipotético no cambia tu costo promedio ni el último cierre de mercado. La cantidad fraccionaria se usa tanto para valorar tu posición como para calcular ganancias y pérdidas potenciales al stop/objetivo.

Los resultados positivos aparecen en verde, negativos en rojo y neutrales en gris claro, acompañados de signos y etiquetas. Las cantidades monetarias se presentan con dos decimales, sin redondear cálculos intermedios; para capital y posición se utiliza aritmética decimal. No se recalcula el costo por compras/ventas adicionales: introduce el promedio actualizado que figure en tu registro. El último cierre ajustado puede diferir de la cotización actual o del precio de ejecución de tu broker.

## MI PORTAFOLIO

Abre **MI PORTAFOLIO · administrar mis posiciones**, encima del análisis técnico. Es independiente del ticker del análisis y permanece disponible aunque falle la consulta del análisis principal.

1. Introduce el ticker, la cantidad (hasta cuatro decimales) y el precio promedio. Pulsa **Agregar o guardar cambios**. Prueba MSFT, 9.42 y 372.42: el capital invertido es US$ 3,508.20.
2. Para editar, introduce el mismo ticker y los nuevos valores; se reemplaza esa posición, sin sumar otra compra. Para eliminar, selecciona el ticker, marca la confirmación y pulsa **Eliminar posición**.
3. Consulta el resumen, las fechas de la última sesión y de consulta (UTC), la distribución por capital/valor y el gráfico de ganancias y pérdidas. **Actualizar precios del portafolio** renueva la caché de precios públicos (15 minutos).
4. Pulsa **Exportar mi copia CSV** y guarda el archivo en una ubicación privada. La aplicación no guarda las posiciones en disco ni en GitHub. Si cierras o pierdes la sesión, puedes perder el registro: exporta primero.
5. Para restaurar una copia, selecciona tu CSV y pulsa **Importar posiciones**. Se agregan tickers nuevos y se actualizan coincidencias; las demás posiciones se conservan. Un CSV inválido se rechaza completo antes de cambiar posiciones.

CSV UTF-8 con comas, punto decimal y columnas en este orden: `ticker,acciones,precio_promedio`. Hasta 500 posiciones y 1 MB por importación. No incluye credenciales ni necesita Interactive Brokers. No subas tus CSV a GitHub: los archivos deben permanecer bajo tu control. La transferencia a Streamlit para importación y su memoria de sesión siguen sujetas a las políticas del proveedor donde despliegues la aplicación.

Si Yahoo Finance no devuelve un cierre, esa posición se muestra como **No disponible**, nunca como cero o como dato demo. El capital invertido incluye todas las posiciones; valor, ganancia/pérdida y rentabilidad incluyen solo aquellas con precio. El resumen se marca **PARCIAL** y la rentabilidad usa únicamente su capital cubierto. No se inventa un valor total completo. Las fechas de cierre permiten detectar historiales antiguos: son cierres ajustados, no cotizaciones en tiempo real. Se mantienen los límites de mercado/moneda de la fuente descritos arriba; el uso previsto son acciones estadounidenses en USD.

## ANÁLISIS INTELIGENTE DE PORTAFOLIO

Dentro de MI PORTAFOLIO, agrega posiciones y abre **ANÁLISIS INTELIGENTE DE PORTAFOLIO**. Pulsa **Consultar / actualizar análisis inteligente**. Usa exclusivamente las posiciones manuales de tu sesión, sin brokers y sin escribir inversiones en disco ni GitHub. CSV y funciones anteriores se mantienen.

- **Diversificación:** pesos según valor actual, exposición por sector Yahoo Finance, tickers con exposición compartida y alerta seleccionable del 15/20/25 %. Sectores ausentes aparecen como No disponible. Si falta un precio, no se calcula una distribución completa.
- **Riesgo:** rendimientos diarios sobre el período común de cinco años disponibles (mínimo 61 cierres comunes); correlación de Pearson; volatilidad muestral anualizada con raíz de 252; máxima caída de una cartera retrospectiva con pesos actuales constantes y rebalanceo diario teórico. No reproduce compras reales ni resultados históricos de tu cuenta. Las series se alinean por fecha local de sesión sin rellenar precios ausentes.
- **Escenarios:** caídas uniformes hipotéticas del 10/20/30 % sobre el valor actual; no son predicciones ni llevan probabilidades.
- **Dividendos:** dividendRate anual por acción reportado por Yahoo × cantidad, dividido entre precio actual (yield) o costo promedio (yield on cost). Anual/12 es un promedio mensual, no un calendario de pagos. La ausencia de dividendRate no se convierte en cero; ingresos disponibles se marcan parciales si faltan posiciones. Dividendos variables, no garantizados, sin impuestos ni conversión monetaria.
- **Rebalanceo:** introduce una aportación hipotética. El reparto proporcional conserva pesos; priorizar posiciones menores nivela sus valores mediante aportaciones sin ventas. Se muestran pesos antes/después y una cota de aportación para diluir la posición mayor. Son alternativas aritméticas, no recomendaciones de compra ni ejecución de órdenes.
- **Puntuación:** configura referencias y pesos para concentración empresarial, sectorial, volatilidad y caída. Cada factor puntúa `100 × max(0, 1 − valor/(2 × referencia))`, limitado a 0–100; la suma es una media ponderada. El valor de referencia equivale a 50 puntos. La fórmula favorece menores concentraciones y variaciones históricas, sin garantizar seguridad o rentabilidad. No se calcula si faltan riesgo o sectores; al menos un peso debe ser positivo.

Los datos públicos del módulo se guardan en caché durante una hora, con fecha UTC de consulta visible; los precios de valoración del portafolio tienen su propia caché de 15 minutos. Actualiza ambos módulos para renovar ambos conjuntos. Yahoo Finance puede omitir campos o restringir consultas. El uso previsto sigue siendo acciones estadounidenses en USD y no se certifica el instrumento ni la moneda. No se requieren nuevas dependencias.

## Corrección de distribuciones TTM: BTCI y TLT

En ANÁLISIS INTELIGENTE, la sección **Distribuciones TTM y dividendos** prioriza los datos manuales válidos sobre Yahoo Finance. Valores iniciales aportados por el usuario desde Interactive Brokers:

| ETF | Anual TTM por acción | Yield TTM reportado | Frecuencia |
| --- | ---: | ---: | --- |
| BTCI | US$ 10.14 | 30.36 % | No especificada |
| TLT | US$ 3.89 | 4.99 % | Mensual |

Fecha de incorporación/actualización inicial: 13/10/2026. No es una verificación independiente del broker ni una fecha de cierre del período TTM. El yield reportado se conserva separado del yield calculado con el último cierre de Yahoo; pueden diferir por fechas y precios de referencia.

Ingreso anual de referencia = acciones actuales × distribución TTM por acción; promedio mensual histórico = anual/12; yield on cost = TTM por acción / costo promedio × 100. Cambiar las acciones del portafolio recalcula automáticamente las cifras sin sobrescribir ninguna posición. Si falta un precio, estos ingresos y el yield on cost siguen disponibles; el yield al cierre queda no disponible. Para otros tickers, Yahoo dividendRate se identifica como tasa anual reportada, no como TTM confirmado.

BTCI incluye aparte el pago confirmado por acción de US$ 0.7184, ex-dividendo 16/09/2026 y pago 18/09/2026. No se suma otra vez al TTM ni se calcula un cobro personal usando acciones actuales: la elegibilidad depende de las acciones con derecho al pago en aquella fecha. Para TLT no se inventa un pago confirmado.

Abre **Actualizar datos manuales sin editar código** para cambiar importes, fuente, fecha, frecuencia y pago confirmado. Exporta **datos de distribuciones JSON** para conservar tus modificaciones y restáuralos desde ese mismo panel después de perder la sesión. La importación valida el archivo completo antes de actualizar registros; no toca el CSV de posiciones. Estos cambios son por sesión, no globales ni persistentes en el servidor. Conserva el JSON bajo tu control y no lo publiques en GitHub.

Las distribuciones son históricas y variables; no garantizan ingresos futuros. El promedio mensual no describe fechas de cobro. Cifras brutas sin impuestos ni retenciones. Pruebas cubren BTCI/TLT, fracciones, prioridad manual, fallback, fechas, edición sin cambiar posiciones y recálculo incluso sin precios.

### Dividendos automáticos para acciones

La consulta de tasas de Yahoo es independiente del éxito del historial de precios. Se utiliza `dividendRate` cuando es válido y se identifica como **tasa anual indicativa**. Si falta, se permite `trailingAnnualDividendRate`, etiquetado como **TTM reportado por Yahoo, no verificado independientemente**. La aplicación no deriva importes del yield ni fija dividendos por ticker. Un valor ausente, booleano o inválido permanece no disponible; un cero explícito válido se conserva.

Los manuales BTCI/TLT siguen teniendo prioridad y se identifican como datos aportados por el usuario, no verificados automáticamente. Los errores de consulta de dividendos se muestran como no disponibles con su motivo; para reintentar una consulta almacenada en caché, pulsa **Consultar / actualizar análisis inteligente**. El yield TTM reportado y la fecha manual no aplican a tasas automáticas y así se indica, en lugar de mostrar `None`. El pago confirmado no se suma a la distribución anual de referencia.

### Fiabilidad y diagnóstico de metadatos Yahoo

Sectores y dividendos usan una caché de datos públicos por sesión separada del historial. Éxitos: hasta una hora (cinco minutos si no hay campos relevantes). Fallos: pausa de 30 segundos o 120 segundos ante límites de consultas; no se guardan como éxito durante una hora. Conexión/timeout y HTTP 5xx admiten hasta tres intentos con esperas de 0.5 y 1 segundo; HTTP 429 hasta dos con espera de 2 segundos. HTTP 401/403 y respuestas inválidas no se repiten inmediatamente. El botón de actualización caduca éxitos, pero respeta las pausas de error para evitar consultas excesivas.

Si falla una actualización se conserva el último resultado válido de la sesión, con etiqueta **Desactualizado**, fecha del dato y fecha del intento. La conservación no sobrevive necesariamente a la pérdida de sesión o reinicio. Un dato ausente no se convierte en cero. La caché no almacena posiciones ni costos y no modifica cálculos históricos o datos manuales.

Los registros del servidor incluyen ticker, tipo de excepción, categoría y estado HTTP si está disponible. No incluyen mensajes completos de excepción, URLs, respuestas, cookies, credenciales ni cantidades. Si yfinance transforma internamente un fallo HTTP en TypeError sin adjuntar la respuesta, se clasifica como respuesta inválida y HTTP no disponible; no se inventa un código. Los campos ausentes de una respuesta estructurada se distinguen de los errores de conexión o autenticación.

Se conserva yfinance 0.2.66: no se ha demostrado que cambiar de versión resuelva el incidente publicado. Las pruebas locales no prueban la recuperación de Streamlit Community Cloud. Para confirmar el incidente allí, despliega la rama después de revisarla, consulta de nuevo y facilita las líneas `Yahoo metadata ticker=... exception=... http=... category=...` del registro de Streamlit junto con fecha/hora, versión desplegada y ticker. No compartas cookies, tokens ni datos privados. Comprueba también la fecha/estado en pantalla para distinguir un dato recuperado de uno antiguo.
