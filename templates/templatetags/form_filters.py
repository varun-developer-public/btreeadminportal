from django import template

register = template.Library()

@register.filter(name='attr')
def set_attr(field, attr_string):
    """Add custom attributes to form fields.
    
    Usage: {{ form.field|attr:"class:custom-class" }}
    """
    attr_name, attr_value = attr_string.split(':')
    return field.as_widget(attrs={attr_name: attr_value})