# -*- coding: utf-8 -*-
"""
Simple callbacks helper.

@author: David Siroky (siroky@dasir.cz)
@license: MIT License (see LICENSE.txt or
          U{http://www.opensource.org/licenses/mit-license.php})
"""

###########################################################################
###########################################################################

class Callback(object):
    def __init__(self):
        self.callbacks = []

    ####################################################

    def add(self, func):
        self.callbacks.append(func)

    ####################################################

    def remove(self, func):
        self.callbacks.remove(func)

    ####################################################

    def __call__(self, *args, **kwargs):
        for callback in self.callbacks:
            callback(*args, **kwargs)
