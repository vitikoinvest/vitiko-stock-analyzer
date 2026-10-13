"""Validación real opcional. Ejecutar python -m scripts.check_finnhub; no está en la suite."""
import json
import os
from finnhub_provider import FinnhubProvider,metric_rows


def main():
    provider=FinnhubProvider(os.environ.get('FINNHUB_API_KEY'))
    rows=[]
    for symbol in ('MSFT','META','HD','SOFI','INTU'):
        for endpoint in ('profile','metrics'):
            result=provider.get(symbol,endpoint)
            row={'ticker':symbol,'endpoint':endpoint,'fuente':'Finnhub','consulta_utc':result.fetched_at,
                 'estado':'no comprobado: falta clave' if not os.environ.get('FINNHUB_API_KEY') else result.error or 'respuesta recibida',
                 'http_error':result.status,'desactualizado':result.stale}
            if result.data is not None:
                row['campos']=list(result.data)
                row['campos_con_valor']=[key for key,value in result.data.items() if value is not None]
                if endpoint=='metrics':row['cobertura']=metric_rows(result.data)
            rows.append(row)
    # stdout: ningún cuerpo completo, clave ni cantidades/costos del usuario.
    print(json.dumps(rows,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
