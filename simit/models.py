from django.db import models
from django.utils.translation import ugettext as _
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from simit.helper import load_url_pattern_names
from tinymce.models import HTMLField
from django.conf import settings
from django.utils.functional import lazy

CUSTOM_TYPES = [
    (1, "TEXT"),
    (2, "DATE"),
    (3, "NUMBER"),
    (4, "RICH TEXT"),
    (5, "BOOLEAN"),
    (6, "CHOICES"),
    (7, "FILE"),
    (8, "IMAGE"),
    (9, "COLOR"),
]


def get_urlconf():
    try:
        if not hasattr(settings, "SIMIT_MENU_URLPATTERNS_MODULE"):
            return list(__import__(settings.ROOT_URLCONF).urls.urlpatterns)
        else:
            return list(__import__(settings.SIMIT_MENU_URLPATTERNS_MODULE).urls.urlpatterns)
    except Exception:
        return []


def dictfetchall(cursor):
    desc = cursor.description
    return [
        dict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()
    ]


class CustomAreaCategory(models.Model):
    name = models.CharField(_('name'), max_length=50, unique=True, db_index=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _('custom area category')
        verbose_name_plural = _('custom area categories')


class CustomArea(models.Model):
    name = models.CharField(_('name'), max_length=100)
    slug = models.CharField(_('slug'), max_length=100, unique=True)
    value = models.TextField(_('value'), )
    type = models.IntegerField(_('type'), choices=CUSTOM_TYPES)
    category = models.ForeignKey("simit.CustomAreaCategory")
    extra = models.TextField(_('extra data'), blank=True)
    description = models.CharField(_('description'), max_length=250, blank=True)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name_plural = _("custom areas")
        verbose_name = _("custom area")


class Page(models.Model):
    name = models.CharField(_('name'), max_length=255)
    content = HTMLField(_('content'), )
    slug = models.SlugField(_('slug'), )
    tags = models.CharField(_('tags'), max_length=255, blank=True)
    description = models.TextField(_('description'), blank=True)
    title = models.CharField(_('title'), max_length=255, blank=True)
    last_modified = models.DateTimeField(_('last modified'), auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = _("pages")
        verbose_name = _("page")

    def __str__(self):
        return self.name


class MenuSection(models.Model):
    name = models.CharField(_('name'), max_length=255)

    class Meta:
        verbose_name_plural = _("menu sections")
        verbose_name = _("menu section")

    def __unicode__(self):
        return self.name


class Menu(MPTTModel):
    title = models.CharField(_('title'), max_length=255)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', verbose_name=_('parent menu'))
    description = models.TextField(_('description'), blank=True)
    url = models.CharField(_('url'), max_length=255, blank=True, null=True)
    page = models.ForeignKey("simit.Page", blank=True, null=True)
    url_name = models.CharField(_('url pattern'), max_length=255, blank=True, null=True,
                                choices=[(name, name) for name in
                                         load_url_pattern_names(
                                             lazy(get_urlconf, list)(),
                                             include_with_args=False)])
    section = models.ForeignKey("simit.MenuSection")
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name_plural = _("menus")
        verbose_name = _("menu")


