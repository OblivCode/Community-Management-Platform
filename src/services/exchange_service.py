import datetime
import requests as http_requests

# Exchange rate cache: {base_code: {"rates": {...}, "fetched_at": datetime}}
_exchange_cache: dict = {}


def get_exchange_rate(from_code: str, to_code: str) -> float:
    """Return exchange rate from_code -> to_code using open.er-api.com. Cached for 1 hour."""
    if from_code == to_code:
        return 1.0
    now = datetime.datetime.utcnow()
    cache = _exchange_cache.get(from_code)
    if not cache or (now - cache['fetched_at']).total_seconds() > 3600:
        try:
            resp = http_requests.get(f'https://open.er-api.com/v6/latest/{from_code}', timeout=5)
            data = resp.json()
            if data.get('result') == 'success':
                _exchange_cache[from_code] = {'rates': data['rates'], 'fetched_at': now}
        except Exception as e:
            print(f'[EXCHANGE] Rate fetch failed: {e}')
            return 1.0
    rates = _exchange_cache.get(from_code, {}).get('rates', {})
    return rates.get(to_code, 1.0)
