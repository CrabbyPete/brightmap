#import phonenumbers
import re
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
@stringfilter
def phonenumber(value):
    usa_phone = re.compile('^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$')
    int_phone = re.compile('^\+(?:[0-9] ?){6,14}[0-9]$')
    string = usa_phone.search(value)
    if string:
        tuple = string.groups()
        return '('+tuple[0]+') '+tuple[1]+'-'+tuple[2]
    else:
        return value
    
"""
The complex way for internation phone numbers    
    number = phonenumbers.parse(value,'US')
    return phonenumbers.format_number(number, phonenumbers.PhoneNumberFormat.NATIONAL)
"""
