from decimal import Decimal
from decimal import InvalidOperation

def is_decimal_number(a: str):
    try:
        decimal_value = Decimal(a)
        return decimal_value > 0
    except InvalidOperation:
        return False