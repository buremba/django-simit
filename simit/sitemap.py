from django.contrib.sitemaps import Sitemap
from simit.models import Page


class PageSitemap(Sitemap):
    changefreq = "never"
    priority = 0.5

    def items(self):
        return Page.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.last_modified


