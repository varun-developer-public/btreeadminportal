from django import template
from core.utils import get_country_codes as get_country_codes_util

register = template.Library()

@register.simple_tag
def get_country_codes():
    return get_country_codes_util()