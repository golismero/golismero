# -*- coding: utf8 -*-

"""
Test-Runner für die Tests gegen standalone
"""

def runtests():
    """
    The test runner for setup.py test usage. This sets up
    a memory database with sqlite3 and runs the tests via
    the django test command.
    """
    from conf import settings
    settings = settings(
        DATABASE_ENGINE='sqlite3',
        DATABASE_NAME=':memory:',
    )

    from django.test.utils import get_runner
    test_runner = get_runner(settings)
    failures = test_runner([], verbosity=1, interactive=True)
    raise SystemExit(failures)

