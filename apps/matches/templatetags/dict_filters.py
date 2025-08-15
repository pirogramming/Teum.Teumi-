# apps/matches/templatetags/dict_filters.py

from django import template

register = template.Library()

@register.filter
def dict_attr(d, key):
    return d.get(key, '')
  