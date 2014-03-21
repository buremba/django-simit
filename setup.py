from setuptools import setup, find_packages

setup(name='django_simit',
      version='0.1',
      description='Yet another Django CMS module',
      url='http://github.com/buremba/simit',
      author='Burak Emre Kabakcı',
      author_email='emrekabakci@gmail.com',
      license='MIT',
      packages=find_packages(),
      zip_safe=False,
      install_requires=[
          'django>=1.5,<1.7', 'feincms', 'git+git://github.com/buremba/django-admin-tools.git'
      ])
