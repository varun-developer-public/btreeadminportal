from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def inspect(obj):
    """
    A template filter to inspect an object's attributes.
    Usage: {{ my_object|inspect }}
    """
    return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}


@register.filter
def get_emi_pending_amount(payment, emi_number):
    """Calculates the pending amount for a specific EMI."""
    emi_amount = getattr(payment, f'emi_{emi_number}_amount', Decimal('0')) or Decimal('0')
    paid_amount = getattr(payment, f'emi_{emi_number}_paid_amount', Decimal('0')) or Decimal('0')
    return emi_amount - paid_amount
