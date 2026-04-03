from django import template

register = template.Library()

@register.simple_tag
def discount_price(price, discount):
    return price - (price*discount/100)

@register.filter
def multiply(value,arg):
    return value*arg