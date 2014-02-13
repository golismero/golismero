# -*- coding: utf8 -*-

"""
This is a collection of utilities to setup the environment
for a standalone django script. This uses option parsers and
fake django settings.
"""

def settings(**kw):
    """
    This function returns the settings that are created for
    a simple sqlite3 database with a given file name. The
    settings are preconfigured so you can actually do normal
    chores with them.

    It uses sqlite3 as default for the database engine because
    that is based on a driver that will be preinstalled in
    modern python installations.

    You can pass in anything you want the settings to carry
    as named parameters - values from the parameter list will
    override potential library defaults.
    """
    from django.conf import settings

    if 'DATABASE_ENGINE' not in kw:
        kw['DATABASE_ENGINE'] = 'sqlite3'
    if 'INSTALLED_APPS' in kw:
        kw['INSTALLED_APPS'] = kw['INSTALLED_APPS'] + ('standalone',)
    else:
        kw['INSTALLED_APPS'] = (
            'standalone',
        )

    settings.configure(**kw)
    return settings

