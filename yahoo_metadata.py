"""Caché de datos públicos por sesión; errores seguros y consultas acotadas."""
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import time

from data import validate_ticker

LOGGER = logging.getLogger(__name__)


class InvalidMetadata(ValueError):
    pass


def classify_error(error):
    status = None
    current = error
    seen = set()
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        response = getattr(current, 'response', None)
        candidate = getattr(response, 'status_code', None)
        if isinstance(candidate, int):
            status = candidate
            break
        current = current.__cause__ or current.__context__
    name = type(error).__name__
    if status in (401, 403):
        return 'autenticación / acceso denegado', status, False
    if status == 429 or name == 'YFRateLimitError':
        return 'límite de consultas', status or 429, True
    if status is not None and status >= 500:
        return 'servicio temporalmente no disponible', status, True
    if isinstance(error, (ConnectionError, TimeoutError)) or any(word in name.lower() for word in ('connection', 'timeout', 'dnserror')):
        return 'conexión', status, True
    if isinstance(error, (InvalidMetadata, TypeError, ValueError)):
        return 'respuesta inválida', status, False
    return 'error de consulta', status, False


@dataclass
class MetadataResult:
    info: dict | None
    fetched_at: str | None
    checked_at: str
    stale: bool
    error: str | None
    exception_type: str | None
    http_status: int | None


class MetadataClient:
    """Solo éxito en caché larga. Los fallos llevan pausa corta sin perder el dato válido."""
    def __init__(self, fetch, clock=time.monotonic, sleep=time.sleep, now=None):
        self.fetch = fetch
        self.clock = clock
        self.sleep = sleep
        self.now = now or (lambda: datetime.now(timezone.utc).isoformat())
        self.valid = {}
        self.errors = {}

    def refresh(self):
        # Caduca éxitos; respeta pausas para que el botón no evada límites de Yahoo.
        for entry in self.valid.values():
            entry['expires'] = 0

    def get(self, ticker):
        symbol = validate_ticker(ticker)
        now = self.clock()
        previous = self.valid.get(symbol)
        failure = self.errors.get(symbol)
        if failure and now < failure['retry_at']:
            return self._failure(previous, failure)
        if previous and now < previous['expires']:
            return MetadataResult(dict(previous['info']), previous['date'], previous['date'], False, None, None, None)
        for attempt in range(3):
            try:
                info = self.fetch(symbol)
                if not isinstance(info, dict) or not info:
                    raise InvalidMetadata('Metadata vacía o no estructurada')
                stamp = self.now()
                # Una respuesta válida sin campos relevantes no se confunde con fallo de red.
                ttl = 3600 if any(info.get(field) is not None for field in ('sector','dividendRate','trailingAnnualDividendRate')) else 300
                self.valid[symbol] = {'info':dict(info), 'date':stamp, 'expires':self.clock()+ttl}
                self.errors.pop(symbol, None)
                return MetadataResult(dict(info), stamp, stamp, False, None, None, None)
            except Exception as error:
                category, status, retryable = classify_error(error)
                # Nunca registra str(error), URLs, cookies, respuestas ni posiciones privadas.
                LOGGER.warning('Yahoo metadata ticker=%s exception=%s http=%s category=%s attempt=%d',
                               symbol, type(error).__name__, status if status is not None else 'no disponible', category, attempt+1)
                retry_limit = 1 if category == 'límite de consultas' else 2
                if retryable and attempt < retry_limit:
                    self.sleep(2. if category == 'límite de consultas' else .5 * 2**attempt)
                    continue
                failure = {'category':category, 'type':type(error).__name__, 'status':status,
                           'date':self.now(), 'retry_at':self.clock()+(120 if category == 'límite de consultas' else 30)}
                self.errors[symbol] = failure
                return self._failure(previous, failure)

    @staticmethod
    def _failure(previous, failure):
        return MetadataResult(dict(previous['info']) if previous else None,
                              previous['date'] if previous else None, failure['date'], bool(previous),
                              failure['category'], failure['type'], failure['status'])
