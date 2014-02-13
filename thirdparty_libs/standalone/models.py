# -*- coding: utf8 -*-

"""
A very simple metaclass to define models in a standalone script
and have those models show up in the standalone.models package.
This allows writing standalone scripts and use the Django ORM
for Database access without jumping through the hoops of
multiple models.

This hack is needed because most django tools need some kind of
installed applications to work. standalone functions as a dummy
application that is patched into dummy dynamic settings at
runtime to make it work.
"""

from django.db.models import *
from django.db.models import base
from django.utils.importlib import import_module

class StandaloneModelBase(base.ModelBase):
    """
    The metaclass for standalone models. This metaclass pushes
    all derived models into the standalone apps models package
    to spoof the management commands and all other tools
    to think there are really models in this package.
    """
    def __new__(cls, name, bases, dct):
        def getMeta(k, default=None):
            try:
                return getattr(dct['Meta'], k)
            except KeyError:
                return default
            except AttributeError:
                return default

        is_script_model = dct.get('__module__', '__main__') == '__main__'
        if not getMeta('abstract'):
            dct['__module__'] = 'standalone.models'
        newClass = base.ModelBase.__new__(cls, name, bases, dct)
        if is_script_model or dct.get('force_install_standalone_models', False):
            mod = import_module('standalone.models')
            setattr(mod, name, newClass)
        return newClass

class StandaloneModel(Model):
    """
    This class is the base class your own models will be
    derived from. Use it just as you would use models.Model
    in a normal Django project.
    """
    __metaclass__ = StandaloneModelBase

    class Meta:
        abstract = True

