#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Import anything you want from the "golismero.api" package.
from golismero.api.config import Config
from golismero.api.logger import Logger

# Possibly the most important part of the API is the data model.
# Here are some example imports.
from golismero.api.data import Relationship
from golismero.api.data.resource.url import URL
from golismero.api.data.information.auth import Username, Password

# Testing plugins are the ones that perform the security tests.
from golismero.api.plugin import TestingPlugin


#------------------------------------------------------------------------------
class TemplatePlugin(TestingPlugin):

    # Don't forget to change your class name!
    # You can name it however you like, as long
    # as it derives from TestingPlugin.


    #--------------------------------------------------------------------------
    def get_accepted_types(self):
        #
        # Here you must specify which data types
        # does your plugin want to receive.
        #
        return [ URL, Relationship(Username, Password) ]


    #--------------------------------------------------------------------------
    def run(self, data):
        #
        #
        # PUT YOUR CODE HERE
        #
        #

        if data.is_instance(URL):
            Logger.log_verbose("Found an URL! %s" % data.url)
        elif data.is_instance(Relationship(Username, Password)):
            Logger.log(
                "Found a valid password! User: %s, Pass: %s" %
                (data[0].name, data[1].password))
        else:
            Logger.log_error("This should never happen...")


    #--------------------------------------------------------------------------
    def check_params(self):
        #
        # Here you can optionally check the configuration and environment.
        # If you see something you don't like, raise any exception.
        # That will cause an error message to be shown and the plugin to be
        # disabled for the current audit.
        #

        VALID_VALUES = ("valid", "values", "for", "this", "argument")
        my_value = Config.plugin_args["my_super_important_argument"]
        if my_value not in VALID_VALUES:
            raise ValueError("Bad value: %r" % my_value)
