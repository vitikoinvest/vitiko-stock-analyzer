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
