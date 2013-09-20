import os
import sys


def run_tests():

    os.environ['DJANGO_SETTINGS_MODULE'] = 'rebar.test_settings'

    from django.conf import settings
    from django.test.utils import get_runner

    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(['rebar'])

    sys.exit(failures)


if __name__ == '__main__':

    run_tests()
