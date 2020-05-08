from django.template.defaulttags import register


def filter_abs(value):
    return abs(value)


register.filter("abs", filter_abs)
