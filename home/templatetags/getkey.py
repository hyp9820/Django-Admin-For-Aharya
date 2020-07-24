from django import template
register = template.Library()

@register.filter
def getkey(mapping, key):
  return mapping.get(key, '')