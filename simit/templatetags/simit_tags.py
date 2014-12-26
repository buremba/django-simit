import re

from django import template
from django.core.exceptions import ObjectDoesNotExist
from django.template import Library
from django.core.cache import cache

from simit.models import CustomArea, Menu


register = Library()
CACHE_TIMEOUT = 60 * 60 * 24


class VariableTag(template.Node):
    def __init__(self, slug, name=None, var_type=None, category=None, description=None):
        self.var_type = var_type
        self.slug = slug
        self.name = name
        self.category = category
        self.description = description

    def render(self, context):
        slug = template.Variable(self.slug).resolve(context)
        cache_key = "simit:variable:%s" % slug
        c = cache.get(cache_key)
        if c is not None:
            return c
        try:
            val = CustomArea.objects.get(slug=slug).value
        except ObjectDoesNotExist:
            val = ""

        cache.set(cache_key, val, CACHE_TIMEOUT)
        return val


@register.tag
def variable(_, token):
    try:
        args = re.findall(r'(\".+?\")', token.contents)
        slug = args[0]
        if len(args) > 1:
            name = args[1]
            var_type = args[2]
            category = args[3] if len(args) > 3 else None
            desc = args[4] if len(args) > 4 else None
            return VariableTag(slug, name, var_type, category, desc)

    except ValueError, e:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]

    return VariableTag(slug)

@register.filter
def variable(slug):
    cache_key = "simit:variable:%s" % slug
    c = cache.get(cache_key)
    if c is not None:
        return c
    try:
        object = CustomArea.objects.get(slug=slug)
        val = object.value
    except ObjectDoesNotExist:
        val = ""

    if object.type == 5:
        val = True if val == "True" else False

    cache.set(cache_key, val, CACHE_TIMEOUT)
    return val

class FetchMenu(template.Node):
    def __init__(self, lookup, var):
        self.variable = var
        self.lookup = lookup

    def render(self, context):
        lookup = template.Variable(self.lookup).resolve(context)

        cache_key = "simit:menu:%s" % lookup
        menus = cache.get(cache_key)
        if menus is None:
            menus = Menu.objects.filter(section__name=lookup)
            cache.set(cache_key, menus, CACHE_TIMEOUT)
        context[self.variable] = menus
        return ''


@register.tag
def getmenu(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires arguments" % token.contents.split()[0]
    m = re.search(r'(.*?) as (\w+)', arg)
    if not m:
        raise template.TemplateSyntaxError, "%r tag had invalid arguments" % tag_name
    format_string, var_name = m.groups()
    return FetchMenu(format_string, var_name)
