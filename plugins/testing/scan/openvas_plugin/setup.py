#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
GoLismero 2.0 - The web knife - Copyright (C) 2011-2013

Authors:
  Daniel Garcia Garcia a.k.a cr0hn | cr0hn<@>cr0hn.com
  Mario Vilas | mvilas<@>gmail.com

Golismero project site: http://golismero-project.com
Golismero project mail: golismero.project<@>gmail.com


This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import argparse
import re
import os
from collections import defaultdict
from functools import partial

# Get the param from a function: script_id(value) -> value
#REG_FUNCTION = r"([\w\W]*%s[\s]*\()([\[\]\.\da-zA-Z\-:\'\"\s]+)(\);[\w\W]*)"
REG_FUNCTION = r"([\w\W]*%s[\s]*\()([\[\]\.\da-zA-Z\-:\'\"\s]+)(\);[\w\W]*)"
#REG_FUNCTION = r"([\w\W]*%s[\s]*\()([\[\]\.\da-zA-Z\-:\'\"\s]+)(\);[\w\W]*)"

# Get value asignated to one array: array['key'] = value -> value
REG_ARRAY = r"([\W\w\s]*%s[\s]*\[[\"\'][\.\da-zA-Z\-:\s]*\"\][\s]*\=[\s]*[\'\"])([\-a-zA-Z\s:\.0-9]+)(\";[\w\W]*)"

# Get value from a string like: 'english: "Some text"' -> Some text
REG_FILTER_PLUGIN_FAMILIES = r"([\w\W\s]*:[\w\W\s]*\"|\')([\w\W\s]*)([\w\W\s]*\"|\'[\w\W\s]*)"
REG_FILTER_REMOVE_QUOTES = r"([\"\']*)([a-zA-Z0-9\-]+)([\"\']*)"


# New regexs
SCRIPT_ID = r"(script_id[\s]*\()([\d]+)([\s]*\))"  # Group 2 -> ID
GENERIC_FUNC = r"(%s[\s]*\([\"\']*)([a-zA-Z0-9\:\.\:\- ]+)([\s]*[\"\']*\))"  # Group 2 -> Function value


#------------------------------------------------------------------------------
#
# DJANGO and databases
#
#------------------------------------------------------------------------------
settings = None

def config_bbdd(path_bbdd):
    """
    Configure database information.

    :param path_bbdd: string with output BBDD.
    :type path_bbdd: str
    """
    if not isinstance(path_bbdd, basestring):
        raise TypeError("Expected basestring, got '%s' instead" % type(path_bbdd))


    from standalone.conf import settings

    global settings

    m_path = os.path.join(os.path.abspath(path_bbdd), "openvas.sqlite3")

    settings = settings(
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': '%s' % m_path,
            }
        },
    )

    #from standalone import models

    ##------------------------------------------------------------------------------
    #class Families(models.StandaloneModel):
        #family_name      = models.CharField(max_length=250, primary_key=True)

    ##------------------------------------------------------------------------------
    #class Plugin(models.StandaloneModel):
        ##plugin_name      = models.CharField(max_length=250)
        #plugin_id        = models.IntegerField(max_length=250, primary_key=True)
        #plugin_file_name = models.CharField(max_length=255)

        #family           = models.ForeignKey(Families)


#------------------------------------------------------------------------------
#
# Aux functions
#
#------------------------------------------------------------------------------
def get_function_value(text, function_name):
    """
    Using regular expresions, get the value from a first function.

    :param text: Text where looking for.
    :type text: str

    :param function_name: Function name.
    :type function_name: str

    :return: Function value.
    :rtype: str
    """
    l_reg = REG_FUNCTION % function_name

    r = re.search(l_reg, text)
    if r:
        return r.group(2)

    return None


#------------------------------------------------------------------------------
def get_array_value(text, array_name):
    """
    Using regular expresions, get the value from a first function.

    :param text: Text where looking for.
    :type text: str

    :param array_name: Function name.
    :type array_name: str

    :return: Function value.
    :rtype: str
    """
    l_reg = REG_ARRAY % array_name

    r = re.search(l_reg, text)
    if r:
        return r.group(2)

    return None


#------------------------------------------------------------------------------
def get_nasl_files_list(path):
    """
    Get all .nasl files from a path

    :param path: Folder where contains .nasl files.
    :type path: str

    :return: an iterator with the file name
    :rtype: iterator(str)
    """


    m_return        = []
    m_return_append = m_return.append
    if path:
        for root, dirs, files in os.walk(path):
            for l_file in files:
                if l_file.endswith(".nasl"):
                    #yield os.path.join(root, l_file)
                    m_return_append(os.path.join(root, l_file))
    else:
        raise ValueError("Path can't be empty.")

    return m_return


#------------------------------------------------------------------------------
def get_nasl_files(path):
    """
    Get all .nasl files from a path

    :param path: Folder where contains .nasl files.
    :type path: str

    :return: an iterator with the file name
    :rtype: iterator(str)
    """
    #yield  os.path.join(path, "macosx_adobe_air_3_6_0_6090.nasl")

    if path:
        for root, dirs, files in os.walk(path):
            for l_file in files:
                if l_file.endswith(".nasl"):
                    yield os.path.join(root, l_file)
    else:
        raise ValueError("Path can't be empty.")


#------------------------------------------------------------------------------
#
# Main code
#
#------------------------------------------------------------------------------
# Attempt to do the proccess multi process
class SharedInfo(object):
    """"""


    #--------------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        self.family = None
        self.file_path = None
        self.plugin_id = None


def process_file(log_file, debug, f_name):
    """"""

    # Process the file
    try:
        m_plugin_family, m_plugin_id = get_plugin_info(f_name)
    except ValueError, e:
        log_file.write("%s\n" % str(e))

        return

    # Filter plugin info
    if m_plugin_family.lower() == "english":
        l = [
            "#" * 80,
             "Plugin family 'english': %s " % str(f_name),
             "\n"
        ]

        # To log file
        log_file.writelines(l)

        # To screen
        print '\n'.join(l)
        return

    # Debug message
    if debug:
        print "Processing: %s (Family) | %s (script_id)" % (m_plugin_family, m_plugin_id)

    from models import Families, Plugin


    f = Families()
    f.family_name = m_plugin_family
    f.save()

    p = Plugin()
    p.plugin_id = m_plugin_id
    p.plugin_file_name = f_name
    p.family = f
    p.save()


    #try:
        #results[m_plugin_family].append([m_plugin_id, f_name])
    #except KeyError:
        #results[m_plugin_family] = d.list()
        #results[m_plugin_family].append([m_plugin_id, f_name])

    #return {m_plugin_family : [m_plugin_id, f_name]}

def parse_files_(path_in, path_out, debug=False):
    """
    Generate de BBDD.
    """
    log_file      = open(os.path.join(path_out, "errors.log"), "w")

    # Split array in N parts
    f = lambda A, n=3: [A[i:i+n] for i in range(0, len(A), n)]


    # Parallel processing
    from multiprocessing import Pool, Manager
    m_correlation = Manager().list()

    func = partial(process_file, log_file, debug)

    files = get_nasl_files(path_in)

    p             = Pool(processes=5)
    p.map(func, files)

    return m_correlation
    #m_correlation = defaultdict(list)
    #for e in f(files, chuncks):
        #r = p.map(func, e)

        ## Filter results
        #for x in r:
            #for fam,v in x.iteritems():
                #m_correlation[fam].append(v)

    #log_file.close()

    #return m_correlation


#
# This code runs oks
#
def parse_files(path_in, path_out, debug=False):
    """
    Generate de BBDD.
    """
    m_correlation = defaultdict(list)

    log_file      = open(os.path.join(path_out, "errors.log"), "w")

    # Parallel processing

    for i, f_name in enumerate(get_nasl_files(path_in)):
        #if i > 6000:
            #break

        # Process the file
        try:
            m_plugin_family, m_plugin_id = get_plugin_info(f_name)
        except ValueError, e:
            log_file.write("%s\n" % str(e))

            continue

        # Filter plugin info
        if m_plugin_family.lower() == "english":
            l = [
                "#" * 80,
                 "Plugin family 'english': %s " % str(f_name),
                 "\n"
            ]

            # To log file
            log_file.writelines(l)

            # To screen
            print '\n'.join(l)
            continue

        # Debug message
        if debug:
            print "%s - Processing: %s (Family) | %s (script_id)" % (str(i), m_plugin_family, m_plugin_id)

        # Store info
        m_correlation[m_plugin_family].append([m_plugin_id, f_name])

    log_file.close()

    return m_correlation


#------------------------------------------------------------------------------
def store_in_bbdd(info, debug=False):
    """
    Store in BBDD information.

    :param info: information to store in BBDD
    :type info: dict({ 'PLUGIN_FAMILY' : list([PLUGIN_ID, PLUGIN_FILE_NAME])})

    :return: True if all done Oks. False otherwise.
    :rtype: bool
    """


    from models import Families, Plugin

    try:

        for k, v in info.iteritems():
            f = Families()
            f.family_name = k
            f.save()

            for plugin in v:
                l_plugin_id = plugin[0]
                l_path      = os.path.split(plugin[1])[1]

                p = Plugin()
                p.plugin_id        = l_plugin_id
                p.plugin_file_name = l_path
                p.family           = f
                p.save()

    except Exception,e:
        if debug:
            print "Error generation BBDD: %s" % str(e)
        return False


    return True


#------------------------------------------------------------------------------
def get_plugin_info(f_name):
    """
    Gets the filename and return the script_id and the family:

    :param f_name: file name
    :type f_name: str

    :return: tupple (family_name, script_id)

    :raises: ValueError
    """
    # File/content vars
    f                   = file(f_name, "rU")
    f_content           = ""

    # Return values
    m_plugin_family     = None
    m_plugin_id         = None

    # Loop var
    cont                = True

    while cont:

        # Read the next 55 lines of the file
        tmp = []
        tmp_append = tmp.append
        for x in range(55):
            v = f.readline()
            if v == '':
                cont = False
            tmp_append(v)
        f_content = ''.join(tmp)

        # Looking for "script_id" value
        if not m_plugin_id:
            m_plugin_id   = get_function_value(f_content, "script_id")

            if m_plugin_id:
                try:
                    int(m_plugin_id)

                    if m_plugin_family:
                        break
                except ValueError:
                    m_plugin_id_tmp = re.search(REG_FILTER_REMOVE_QUOTES, m_plugin_id)

                    if m_plugin_id_tmp:
                        m_plugin_id = m_plugin_id_tmp.group(2)

                        if m_plugin_family:
                            break
                    else:
                        m_plugin_id = None

        # Looking for "family"" in arrays
        m_info_array        = get_array_value(f_content, "family")

        if m_info_array:
            m_plugin_family = m_info_array
            break
        else:
            # Get family name
            m_plugin_family_tmp   = get_function_value(f_content, "script_family")

            if m_plugin_family_tmp:
                # Filter and prepare the plugin_family
                m_plugin_family = re.search(REG_FILTER_PLUGIN_FAMILIES, m_plugin_family_tmp)
                if m_plugin_family:
                    m_plugin_family = m_plugin_family.group(2).replace("\"", "").replace("'","")

                    if m_plugin_id:
                        break
                else:
                    m_plugin_family = m_plugin_family_tmp
                    if m_plugin_family:
                        m_plugin_family = m_plugin_family.replace("\"", "").replace("'","")



    f.close()

    # Errors
    if not m_plugin_family:
        raise ValueError("Error processing file %s. Family '%s' can't be processed." % (f_name, m_plugin_family))
    else:
        m_plugin_family = m_plugin_family.strip()
    if not m_plugin_id:
        raise ValueError("Error processing file %s. Plugin ID '%s' can't be processed." % (f_name, m_plugin_id))
    else:
        m_plugin_id = m_plugin_id.strip()

    return (m_plugin_family, m_plugin_id)


#------------------------------------------------------------------------------
def run_tests(path):
    """Test a .nasl plugin"""

    plugin1 = os.path.join(path, "/Users/Dani/Downloads/openvas-nvt-feed-current/FormMail_detect.nasl")
    print get_plugin_info(plugin1)


#------------------------------------------------------------------------------
def main(args):
    """"""

    path_openvas_plugins = args.OPENVAS_PLUGINS
    path_out             = args.OUTPUT_BBDD
    debug                = args.DEBUG
    remove_old           = args.REMOVE_OLD

    if not os.path.isdir(path_out):
        print
        print "[!] Output database must be a folder, not a file."
        print
        exit(1)


    if remove_old:
        l_bbdd_name = os.path.join(path_out, "openvas.sqlite3")
        if os.path.exists(l_bbdd_name):
            if debug:
                print "Deleting old OpenVAS database: '%s'." % l_bbdd_name
            os.remove(l_bbdd_name)

    #
    # Config and generate BBDD
    #
    config_bbdd(path_out)

    # This import only can be done after config_bbdd execution
    from models import Families, Plugin

    # Generate BBDD
    from django.core.management import call_command
    call_command("syncdb") # Creates the BBDD

    if args.ONLY_TESTS:
        run_tests(path_openvas_plugins)
    else:
        info = parse_files(path_openvas_plugins, path_out, debug=debug)
        if store_in_bbdd(info, debug):
            print "Database generated well"
        else:
            print "Error while generating dabatase"



if __name__=='__main__':

    parser = argparse.ArgumentParser(description='Generates OpenVAS database.')
    parser.add_argument('-o', dest="OUTPUT_BBDD", help="output database folder.", default=os.path.abspath(os.path.split(__file__)[0])) # Current directory default
    parser.add_argument('-p', dest="OPENVAS_PLUGINS", help="openvas plugins path", required=True)
    parser.add_argument('--remove-old', action="store_true", dest="REMOVE_OLD", help="remove old OpenVAS database")
    parser.add_argument('--test', action="store_true", dest="ONLY_TESTS", help="only run tests", default=False)
    parser.add_argument('-v', action="store_true", dest="DEBUG", help="enable debug information", default=False)

    args = parser.parse_args()

    main(args)
