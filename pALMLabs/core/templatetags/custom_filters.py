from django import template

register = template.Library()

@register.filter
def floatval(val):
    try:
        return float(val)
    except:
        return 0
