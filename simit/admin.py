import os
from django.conf import settings
from django.conf.urls import patterns, url
from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from feincms.admin.tree_editor import TreeEditor
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from admin_tools.admin import RichModelAdmin
from forms import VariableForm
from models import CustomArea, CustomAreaCategory, Page, Menu, MenuSection
from django.core.cache import cache


class CustomAreaAdmin(admin.ModelAdmin):
    search_fields = ['name']
    exclude = ('value', )
    prepopulated_fields = {'slug': ('name',), }
    list_filter = ('type',)

    def get_urls(self):
        urls = super(CustomAreaAdmin, self).get_urls()
        my_urls = patterns('', url(r'^settings/?([0-9]+)?$', self.admin_site.admin_view(self.settings),
                                   name="simit_customarea_settings"))
        return my_urls + urls

    def save_model(self, request, obj, form, change):
        if change:
            cache.delete("simit:variable:%s" % obj.slug)
        return super(CustomAreaAdmin, self).save_model(request, obj, form, change)

    def settings(self, request, category):
        categories = CustomAreaCategory.objects.all()

        if category is None:
            if categories.count() > 0:
                category = categories[0]
            else:
                return render_to_response('admin/customarea_edit.html', {"title": _('Custom Area')},
                                          RequestContext(request))
        else:
            category = get_object_or_404(CustomAreaCategory, pk=category)

        q = {'fieldQuerySet': CustomArea.objects.filter(category=category.id)}

        if request.method == "GET":
            form = VariableForm(**q)
        elif request.method == "POST":
            form = VariableForm(request.POST, request.FILES, **q)
            if form.is_valid():
                for key, value in form.cleaned_data.iteritems():
                    item = CustomArea.objects.get(slug=key)
                    from django.contrib.admin.models import LogEntry, CHANGE
                    from django.utils.encoding import force_unicode

                    val = unicode(value)
                    if item.value != val:
                        LogEntry.objects.log_action(
                            user_id=request.user.pk,
                            content_type_id=ContentType.objects.get_for_model(CustomArea).pk,
                            object_id=item.pk,
                            object_repr=force_unicode(item),
                            action_flag=CHANGE,
                            change_message="Changed from settings page"
                        )
                        cache.delete('simit:variable:%s' % key)
                        if item.type in [7, 8]:
                            val = default_storage.save(os.path.join("simit/images", val), ContentFile(value.read()))

                        item.value = val

                        item.save()
                return HttpResponseRedirect(request.get_full_path())

        return render_to_response('admin/customarea_edit.html',
                                  {"categories": categories, "title": _('Custom Area'), "activeCategory": category,
                                   "opts": CustomArea._meta, "VariableForm": form},
                                  RequestContext(request))


class PageAdmin(ModelAdmin):
    prepopulated_fields = {'slug': ('name',), }
    search_fields = ('name',)
    fieldsets = (
        ('', {
            'fields': ('name', 'content')
        }),
        ('Page Seo Settings', {
            'classes': ('collapse',),
            'fields': ('title', 'description', 'tags', 'slug')
        }),
    )


class MainMenuFilter(admin.SimpleListFilter):
    title = _('parent menu')
    parameter_name = 'main_cat'

    def lookups(self, request, model_admin):
        model = model_admin.model
        param = request.GET.get(self.parameter_name, None)
        if param is None:
            main_objects = model.objects.filter(level=0)
        else:
            main_objects = model.objects.filter(parent=param)
        arr = []
        for obj in main_objects:
            arr.append((obj.id, obj))

        return arr

    def queryset(self, request, queryset):
        if self.value() is not None:
            children = queryset.model.objects.get(pk=self.value()).get_descendants()
            return children & queryset


class MenuAdmin(TreeEditor, RichModelAdmin):
    list_filter = ("parent", )
    require_one_of = ('page', 'url_name', 'url')
    search_fields = ('title', 'description')
    list_filter = ('section', MainMenuFilter)

    def _actions_column(self, page):
        preview_url = "../../r/%s/%s/" % (ContentType.objects.get_for_model(self.model).id, page.id)
        actions = super(MenuAdmin, self)._actions_column(page)
        actions.insert(0,
                       u'<a href="add/?parent=%s" title="%s"><img src="%sfeincms/img/icon_addlink.gif" alt="%s"></a>' % (
                           page.pk, _('Add child page'), settings.STATIC_URL, _('Add child page')))
        actions.insert(0, u'<a href="%s" title="%s"><img src="%sfeincms/img/selector-search.gif" alt="%s" /></a>' % (
            preview_url, _('View on site'), settings.STATIC_URL, _('View on site')))
        return actions

    def __unicode__(self):
        return self.name

    def save_model(self, request, obj, form, change):
        if change or obj.pk is None:
            cache.delete("simit:menu:%s" % obj.section.name)
        return super(MenuAdmin, self).save_model(request, obj, form, change)


class MenuSectionAdmin(ModelAdmin):
    search_fields = ('name',)

    def save_model(self, request, obj, form, change):
        if change:
            cache.delete("simit:menu:%s" % MenuSection.objects.get(id=obj.id).name)
        return super(MenuSectionAdmin, self).save_model(request, obj, form, change)


admin.site.register(Menu, MenuAdmin)
admin.site.register(MenuSection, MenuSectionAdmin)
admin.site.register(CustomArea, CustomAreaAdmin)
admin.site.register(CustomAreaCategory)
admin.site.register(Page, PageAdmin)
