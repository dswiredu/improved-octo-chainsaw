from django import template

register = template.Library()

@register.filter
def floatval(val):
    try:
        return float(val)
    except:
        return 0


@register.filter
def abs(val):
    try:
        return abs(float(val))
    except:
        return val