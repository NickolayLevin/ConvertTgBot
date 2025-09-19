import requests
import json
from config import keys
from functools import lru_cache

class APIException(Exception):
    pass

class Converter:
    @staticmethod
    @lru_cache(maxsize=100)
    def _fetch_rate(base: str, quote: str) -> float:
        # Внутренний метод для получения курса 1 единицы base в quote
        try:
            base_ticker = keys[base]
            quote_ticker = keys[quote]
            # Адаптируйте URL под ваше API, например, для exchangeratesapi.io
            r = requests.get(
                f'https://v6.exchangerate-api.com/v6/0c6bfd9bf83175dcc4574f71/pair/{base_ticker}/{quote_ticker}/1')
            r.raise_for_status()
            data = json.loads(r.content)
            rate = data['conversion_result']
            return rate
        except KeyError:
            raise APIException(f'Не удалось обработать валюту {base} или {quote}')
        except Exception as e:
            raise APIException(f'Ошибка API: {e}')

    @staticmethod
    def get_price(base: str, quote: str, amount: str) -> float:
        if base == quote:
            raise APIException('Невозможно перевести одинаковые валюты.')
        if base not in keys or quote not in keys:
            raise APIException(f'Недоступная валюта: {base} или {quote}. Используйте /values')
        try:
            amount = float(amount)
        except ValueError:
            raise APIException(f'Не удалось обработать количество {amount}')
        rate = Converter._fetch_rate(base, quote)
        return rate * amount
