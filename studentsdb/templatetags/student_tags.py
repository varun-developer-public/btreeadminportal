from django import template

register = template.Library()

@register.filter
def get_attribute(obj, attr):
    return getattr(obj, attr, "")


@register.filter
def get_emi_pending_amount(payment, emi_number):
    """
    Calculates the pending amount for a specific EMI.
    """
    try:
        emi_amount = getattr(payment, f'emi_{emi_number}_amount') or Decimal('0')
        emi_paid_amount = getattr(payment, f'emi_{emi_number}_paid_amount') or Decimal('0')
        pending_amount = emi_amount - emi_paid_amount
        return pending_amount if pending_amount > 0 else Decimal('0')
    except (AttributeError, TypeError):
        return Decimal('0')


@register.filter
def replace(value, arg):
    """
    Replacing filter
    Use `{{ "aaa"|replace:"a|b" }}`
    """
    if len(arg.split('|')) != 2:
        return value

    what, to = arg.split('|')
    return value.replace(what, to)
