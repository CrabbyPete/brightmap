from django import template

register = template.Library()

@register.filter
def fortyfive(value):
    return "%.2f" % ( float(value) *.45 )