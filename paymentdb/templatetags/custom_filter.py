from django import template

register = template.Library()

@register.filter
def get_dynamic(obj, attr):
    return getattr(obj, attr, None)

@register.filter
def get_field(form, name):
    return form[name]

@register.simple_tag
def emi_value(payment, emi_number, field_name):
    attr = f"emi_{emi_number}_{field_name}"
    val = getattr(payment, attr, None)
    print(f"DEBUG: {attr} = {val}")
    if val is None:
        return ""
    return val
