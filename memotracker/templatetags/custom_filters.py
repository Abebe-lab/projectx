from django import template

register = template.Library()

@register.filter
def get_val(dictionary, key):
    return dictionary.get(key)


@register.filter
def get_route_status(instance, request):
    return instance.get_route_status(request)
