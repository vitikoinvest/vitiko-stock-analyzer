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

Se instalaron las dependencias y se comprobó el arranque de Streamlit, su endpoint de salud y las pruebas automatizadas de cálculos e interfaz. La prueba real de MSFT devolvió `CONNECT tunnel failed, response 403`: el proxy de red bloquea Yahoo Finance. Esto impide verificar precios reales en este entorno hasta aplicar la configuración de red; la demo funciona y la aplicación muestra el error sin sustituir datos.

Se guardó un borrador con instrucciones de instalación/arranque y acceso a `query1.finance.yahoo.com`, `query2.finance.yahoo.com`, `fc.yahoo.com`, `guce.yahoo.com` y `finance.yahoo.com`. Revisa y guarda esos cambios en los ajustes del entorno, y publica el entorno. Después hay que repetir la consulta real para confirmar el acceso; guardar un borrador no cambia la red de la máquina actual.
