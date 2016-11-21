#!/usr/bin/python
# -*- coding: utf-8 -*-

from django import template

register = template.Library()


@register.filter
def break_line(value, arg):
    if value:
        return '\n'.join([value[i:arg+i] for i in range(0, len(value), arg)])
    else:
        return '...'
