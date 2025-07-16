from django import template

register = template.Library()

@register.filter
def get_dynamic(obj, attr):
    return getattr(obj, attr, None)

@register.filter
def get_field(form, name):
    return form[name]
