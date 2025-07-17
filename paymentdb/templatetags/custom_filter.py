from django import template

register = template.Library()

@register.simple_tag
def get_payment_attr(payment, emi_number, field_name):
    """Gets a payment attribute dynamically."""
    attr_name = f"emi_{emi_number}_{field_name}"
    return getattr(payment, attr_name, "")

@register.simple_tag
def get_form_field(form, emi_number, field_name):
    """Gets a form field dynamically."""
    field_name = f"emi_{emi_number}_{field_name}"
    return form[field_name]

@register.filter
def is_emi_fully_paid(payment, emi_number):
    """Checks if an EMI is fully paid."""
    return payment.is_emi_fully_paid(emi_number)

@register.filter
def get_attribute(obj, arg):
    """
    Gets an attribute of an object dynamically.
    Usage: {{ object|get_attribute:"attribute_name" }}
    """
    attributes = arg.split('.')
    for attr in attributes:
        if hasattr(obj, attr):
            obj = getattr(obj, attr)
        else:
            return None
    return obj

@register.filter
def subtract(value, arg):
    """Subtracts the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value