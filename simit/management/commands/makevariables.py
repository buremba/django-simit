import fnmatch
import os
import re
from optparse import make_option
from django.core.management.base import NoArgsCommand
from django.core.management.utils import handle_extensions
from django.db import IntegrityError
from django.template import Template
from simit.models import CustomArea, CustomAreaCategory, CUSTOM_TYPES
from simit.templatetags.simit_tags import VariableTag
from django.conf import settings

plural_forms_re = re.compile(r'^(?P<value>"Plural-Forms.+?\\n")\s*$', re.MULTILINE | re.DOTALL)
reserve_variable_options = {t[1]: t[0] for t in CUSTOM_TYPES}

def is_constant(variable):
    return variable[0] == variable[-1]

class Command(NoArgsCommand):
    option_list = NoArgsCommand.option_list + (
        make_option('--all', '-a', action='store_true', dest='all',
                    default=False, help='Updates the message files for all existing locales.'),
        make_option('--symlinks', '-s', action='store_true', dest='symlinks',
                    default=False,
                    help='Follows symlinks to directories when examining source code and templates for translation strings.'),
        make_option('--ignore', '-i', action='append', dest='ignore_patterns',
                    default=[], metavar='PATTERN',
                    help='Ignore files or directories matching this glob-style pattern. Use multiple times to ignore more.'),
        make_option('--no-default-ignore', action='store_false', dest='use_default_ignore_patterns',
                    default=True, help="Don't ignore the common glob-style patterns 'CVS', '.*', '*~' and '*.pyc'."),
    )
    help = ("Runs over the entire source tree of the current directory and "
            "pulls out all strings marked for simit variables. It creates (or updates) the variables "
            "in your templates")

    def handle_noargs(self, *args, **options):
        extensions = options.get('extensions')
        self.symlinks = options.get('symlinks')
        ignore_patterns = options.get('ignore_patterns')
        if options.get('use_default_ignore_patterns'):
            ignore_patterns += ['CVS', '.*', '*~', '*.pyc']
        self.ignore_patterns = list(set(ignore_patterns))

        exts = extensions if extensions else ['html', 'txt']
        self.extensions = handle_extensions(exts)

        variable_slug = set()
        for app in settings.INSTALLED_APPS:
            try:
                module_path = os.path.join(os.path.dirname(__import__(app).__file__), 'templates')
                for filename in self.find_files(module_path):
                    try:
                        t = Template(open(filename).read())
                    except Exception, e:
                        self.stdout.write("%s couldn't parse: %s\n" % (filename, e.message))

                    def process(nodelist):
                        for node in nodelist:
                            if node.__class__ == VariableTag and node.var_type is not None:
                                if node.slug in variable_slug:
                                    continue
                                if not (is_constant(node.slug) and (node.category is not None and is_constant(node.category)) and is_constant(node.var_type)):
                                    self.stdout.write('found %s in %s %s but it seems like a variable. passing... \n' % (node.slug, filename, node.source[1]))
                                    continue
                                slug = node.slug.strip('"')
                                category = node.category.strip('"')
                                var_type = node.var_type.strip('"')
                                if category is not None:
                                    category, _ = CustomAreaCategory.objects.get_or_create(name=category)
                                else:
                                    category, _ = CustomAreaCategory.objects.get_or_create(name="General")

                                if var_type in reserve_variable_options:
                                    type_id = reserve_variable_options[var_type]
                                else:
                                    continue

                                variable_slug.add(node.slug)

                                description = node.description.strip('"') if is_constant(node.description) else None
                                name = node.name.strip('"') if is_constant(node.name) else None

                                try:
                                    CustomArea(slug=slug, type=type_id, name=name, category=category,
                                               description=description).save()
                                except IntegrityError:
                                    #self.stdout.write("found %s but it's already saved in database\n" % (node.slug,))
                                    variable = CustomArea.objects.get(slug=slug)
                                    if variable.description is None and description is not None:
                                        variable.description = node.description
                                        variable.save()
                                    continue

                                self.stdout.write('found %s in %s %s\n' % (node.slug, filename, node.source[1]))

                            elif hasattr(node, 'nodelist') and node.nodelist is not None:
                                process(node.nodelist)

                    process(t.nodelist)
            except ImportError:
                continue

    def find_files(self, root):
        """
        Helper method to get all files in the given root.
        """

        def is_ignored(path, ignore_patterns):
            """
            Check if the given path should be ignored or not.
            """
            filename = os.path.basename(path)
            ignore = lambda pattern: fnmatch.fnmatchcase(filename, pattern)
            return any(ignore(pattern) for pattern in ignore_patterns)

        dir_suffix = '%s*' % os.sep
        norm_patterns = [p[:-len(dir_suffix)] if p.endswith(dir_suffix) else p for p in self.ignore_patterns]
        all_files = []
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=self.symlinks):
            for dirname in dirnames[:]:
                if is_ignored(os.path.normpath(os.path.join(dirpath, dirname)), norm_patterns):
                    dirnames.remove(dirname)
            for filename in filenames:
                if not is_ignored(os.path.normpath(os.path.join(dirpath, filename)), self.ignore_patterns):
                    all_files.append(os.path.join(dirpath, filename))
        return sorted(all_files)
