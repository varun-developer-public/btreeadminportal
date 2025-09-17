from django import template
from datetime import datetime

register = template.Library()

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

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

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

@register.filter
def format_name(value):
    """Removes 'nan' from a string."""
    if isinstance(value, str) and 'nan' in value.lower():
        return value.lower().replace('nan', '').strip()
    return value

@register.filter(name='attr')
def attr(field, css):
    attrs = {}
    definition = css.split(',')

    for d in definition:
        if ':' in d:
            key, val = d.split(':')
            attrs[key.strip()] = val.strip()

    return field.as_widget(attrs=attrs)

@register.filter
def intcomma(value):
    """
    Converts an integer to a string containing commas in the Indian numbering system.
    For example, 100000 becomes '1,00,000'.
    """
    try:
        val = int(value)
        s = str(val)
        if len(s) <= 3:
            return s
        last_three = s[-3:]
        other_digits = s[:-3]
        return ','.join([other_digits[max(0, i-2):i] for i in range(len(other_digits), 0, -2)][::-1]) + ',' + last_three
    except (ValueError, TypeError):
        return value
@register.filter
def format_time(time_str):
    if isinstance(time_str, str):
        try:
            return datetime.strptime(time_str, '%H:%M').strftime('%I:%M %p')
        except ValueError:
            return time_str
    return time_str