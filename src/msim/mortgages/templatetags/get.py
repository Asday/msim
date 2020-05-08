from django.template.defaulttags import register


@register.filter
def get(collection, key):
    return collection.get(key)
