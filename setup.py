from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
NEWS = open(os.path.join(here, 'NEWS.txt')).read()


version = '0.4'


setup(name='rebar',
      version=version + '+eventbrite.2',
      description="",
      long_description=README + '\n\n' + NEWS,
      classifiers=[
          'License :: OSI Approved :: BSD License',
      ],
      keywords='',
      url='https://github.com/eventbrite/rebar',
      license='BSD',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          'Django',
      ],
      tests_require=[
          'django-discover-runner',
          'docsix',
          'mock',
      ],
      test_suite='rebar.tests.run_tests',
)
