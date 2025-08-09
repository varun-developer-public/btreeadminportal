from django import template
from coursedb.forms import TopicFormSet

register = template.Library()

@register.filter
def get_topic_formset(module_instance, post_data=None):
    return TopicFormSet(post_data, instance=module_instance, prefix=f'topics-module-{module_instance.pk}')

@register.filter
def with_prefix(formset, prefix):
    formset.prefix = prefix
    return formset