from django.template.defaulttags import register


@register.filter
def add(a, b):
    return a + b
