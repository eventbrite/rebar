import doctest
import glob
import os
import sys

import manuel.codeblock
import manuel.doctest
import manuel.testing

from rebar.tests.manuel_ext import (
    testcode,
)


def setup():
    """Perform test runner setup.

    This is its own function so we can easily call it from doctest
    ``testsetup`` blocks.

    """

    os.environ['DJANGO_SETTINGS_MODULE'] = 'rebar.test_settings'

    import django
    if django.VERSION >= (1, 7):
        # initialize the app regsitry
        django.setup()


def get_doctest_suite():
    """Return the doctest suite."""

    m = manuel.doctest.Manuel(
        optionflags=doctest.ELLIPSIS,
    )
    m += manuel.codeblock.Manuel()
    m += testcode.Manuel()

    return manuel.testing.TestSuite(
        m,
        *[
            os.path.join(
                os.getcwd(),
                path,
            )
            for path in glob.glob('docs/*.rst')
        ]
    )


def run_tests():

    setup()

    from django.conf import settings
    from django.test.utils import get_runner

    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    failures = test_runner.run_tests(
        ['rebar'],
        extra_tests=get_doctest_suite(),
    )

    sys.exit(failures)


if __name__ == '__main__':

    run_tests()
