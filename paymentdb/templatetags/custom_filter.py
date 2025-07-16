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
