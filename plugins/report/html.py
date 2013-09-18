#!/usr/bin/env python
# -*- coding: utf-8 -*-

__license__ = """
GoLismero 2.0 - The web knife - Copyright (C) 2011-2013

Authors:
  Daniel Garcia Garcia a.k.a cr0hn | cr0hn<@>cr0hn.com
  Mario Vilas | mvilas<@>gmail.com

Golismero project site: https://github.com/golismero
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

from golismero.api.audit import get_audit_times
from golismero.api.config import Config
from golismero.api.data import Data
from golismero.api.data.db import Database
from golismero.api.data.resource import Resource
from golismero.api.logger import Logger
from golismero.api.plugin import ReportPlugin

from os.path import join, dirname
from collections import Counter, defaultdict
import datetime


#------------------------------------------------------------------------------
class HTMLReport(ReportPlugin):
    """
    Plugin to generate HTML reports.
    """

    # The main porperties of the resources
    MAIN_RESOURCES_PROPERTIES = {
        'URL'           : 'url',
        'BASE_URL'      : 'url',
        'FOLDER_URL'    : 'url',
        'DOMAIN'        : 'hostname',
        'IP'            : 'address',
        'EMAIL'         : 'address'
    }

    # This properties/methods are the common info for the vulnerability types.
    PRIVATE_INFO_VULN = ['DEFAULTS', 'TYPE', 'add_information', 'RESOURCE',
                         'add_link', 'add_resource', 'add_vulnerability', 'associated_informations',
                         'associated_resources', 'associated_vulnerabilities',
                         'data_type', 'discovered', 'false_positive', 'get_associated_informations_by_category',
                         'get_associated_resources_by_category', 'get_associated_vulnerabilities_by_category',
                         'get_linked_data', 'get_links', 'identity', 'impact', 'is_in_scope', 'linked_data',
                         'links', 'max_data', 'max_informations', 'max_resources', 'max_vulnerabilities',
                         'merge', 'min_data', 'min_informations', 'min_resources', 'min_vulnerabilities',
                         'references', 'reverse_merge', 'risk', 'severity', 'validate_link_minimums', 'vulnerability_type',
                         'resource_type', 'resolve', 'resolve_links', 'find_linked_data', 'depth', 'taxonomies', 'data_subtype',
                         'title']

    # This properties/methods are the common info for the vulnerability types.
    PRIVATE_INFO_RESOURCES = ['DEFAULTS', 'TYPE', 'add_information', 'RESOURCE',
                              'add_link', 'add_resource', 'add_vulnerability', 'associated_informations',
                              'associated_resources', 'associated_vulnerabilities',
                              'data_type', 'discovered', 'get_associated_informations_by_category',
                              'get_associated_resources_by_category', 'get_associated_vulnerabilities_by_category',
                              'get_linked_data', 'get_links', 'identity', 'impact', 'is_in_scope', 'linked_data',
                              'links', 'max_data', 'max_informations', 'max_resources', 'max_vulnerabilities',
                              'merge', 'min_data', 'min_informations', 'min_resources', 'min_vulnerabilities',
                              'references', 'reverse_merge', 'risk', 'severity', 'validate_link_minimums', 'vulnerability_type',
                              'resource_type', 'resolve', 'resolve_links', 'find_linked_data', 'depth', 'taxonomies', 'data_subtype']



    #--------------------------------------------------------------------------
    #
    # Aux functions
    #
    #--------------------------------------------------------------------------
    def is_supported(self, output_file):
        return output_file and (
            output_file.lower().endswith(".html") or
            output_file.lower().endswith(".htm")
        )


    def common_get_resources(self, data_type=None, data_subtype=None):
        """
        Get a list of datas.

        :return: List of resources.
        :rtype: list(Resource)
        """
        # Get each resource
        m_resource = None
        m_len_urls = Database.count(data_type, data_type)
        if m_len_urls < 200:   # increase as you see fit...
            # fast but memory consuming method
            m_resource   = Database.get_many( Database.keys(data_type=data_type, data_subtype=data_subtype))
        else:
            # slow but lean method
            m_resource   = Database.iterate(data_type=data_type, data_subtype=data_subtype)

        return m_resource




    #--------------------------------------------------------------------------
    def generate_report(self, output_file):
        Logger.log_verbose("Writing HTML report to file: %s" % output_file)

        #
        # configure django
        #

        import django.conf
        django.conf.settings.configure(
            TEMPLATE_DIRS = (join(dirname(__file__), './html_report'),)
        )

        from django.template import Template, loader, Context
        from django.conf import settings

        c = Context()
        t = loader.get_template(template_name="template.html")

        #
        # Fill the context
        #

        # Audit name
        c['audit_name'] = Config.audit_name

        # Start date
        start_time, stop_time = get_audit_times()
        c['start_date']       = datetime.datetime.fromtimestamp(start_time) if start_time else "Unknown"
        c['end_date']         = datetime.datetime.fromtimestamp(stop_time)  if stop_time  else "Interrupted"

        # Execution time
        if start_time and stop_time and start_time < stop_time:
            td      = datetime.datetime.fromtimestamp(stop_time) - datetime.datetime.fromtimestamp(start_time)
            days    = td.days
            hours   = td.seconds // 3600
            minutes = (td.seconds // 60) % 60
            seconds = td.seconds
            c['execution_time'] = "%d days %d hours %d minutes %d seconds" % (days, hours, minutes, seconds)
        else:
            c['execution_time'] = "Unknown"

        # Targets
        # XXX FIXME: the HTML template only knows how to show URL targets! :(
        targets = Config.audit_scope.get_targets()
        targets = [
            x.url for x in targets
                  if   x.data_type == x.TYPE_RESOURCE and
                   x.resource_type == x.RESOURCE_URL
        ]
        c['targets'] = targets

        # Fill the vulnerabilities summary
        self.fill_summary_vulns(c)

        # Fill the info of the resources
        self.fill_content_resource(c)

        # Fill the info of the resources
        self.fill_content_vuln(c)

        #
        # Write the output
        #
        m_rendered = t.render(c)

        f = open(output_file, "w")
        f.write("%s" % m_rendered.encode("utf-8"))
        f.close()

    #----------------------------------------------------------------------
    def fill_summary_vulns(self, context):
        """
        Fill the context var with summary of the vulnerabilities.

        :param context: Context var to fill.
        :type context: Context
        """

        m_all_vulns   = self.common_get_resources(data_type=Data.TYPE_VULNERABILITY)

        m_results          = {}

        # Total vulns
        m_results['total'] = 0

        # Count each type of vuln
        m_counter = Counter()

        # Init
        m_counter['critical']       = 0
        m_counter['high']           = 0
        m_counter['middle']         = 0
        m_counter['low']            = 0
        m_counter['informational']  = 0

        # Vulnerabilities by type
        for l_v in m_all_vulns:
            if l_v.false_positive:
                continue
            m_counter['total']   += 1
            m_counter[l_v.level] += 1

        m_counter['no_vulns'] = int(bool(m_results['total'] == 0))

        for k,v in m_counter.iteritems():
            m_results[k] = v

        context['summary_vulns']     = m_results



    #----------------------------------------------------------------------
    #
    # Concrete displayer for resources
    #
    #----------------------------------------------------------------------
    def fill_content_resource(self, context):
        """
        Fill the context var with the "resource" information.

        This method generates a list as format:

        [
            {
                'resource_type' : "URL",

                'info'          : [
                    # Resource 1
                    {
                        # Resource info
                        'main_info' : "http://www.mytest.site.com",

                        'properties' : [
                           {
                              'name'  : 'name property 1',
                              'value'  : 'value property 1',
                           },
                        ],

                        'associated_vulns' : [
                           {
                              'vuln_name': 'name of vuln',
                              'vuln_properties: [
                                 {
                                    'name': 'name of property 1',
                                    'value' : 'value of property 1'
                                 }
                              ]
                           }
                        ]

                        # Vulns
                        'vulns'  : [
                            {
                                'level'   : 'high',
                                'number'  : '4'
                            }
                        ]
                    }
                ]
            }
        ]

        :param context: Context var to fill.
        :type context: Context
        """

        m_results        = []
        m_results_append = m_results.append

        # Get all type of resources
        #
        # FIXME: take the BaseURL and FolderUrl resources, unify their vulns and put them in the common URL resource
        #
        m_all_resources = set([x for x in dir(Resource) if x.startswith("RESOURCE") and x != "RESOURCE_BASE_URL" and x != "RESOURCE_FOLDER_URL"])

        for l_resource in m_all_resources:
            l_res_result = {}

            # Get resources URL resources
            resource = self.common_get_resources(Data.TYPE_RESOURCE, getattr(Resource, l_resource))

            if not resource:
                continue

            l_res_result['resource_type'] = l_resource.replace("RESOURCE_", "").lower().replace("_", " ").capitalize()
            l_res_result['info']          = []

            # ----------------------------------------
            # Discovered resources
            # ----------------------------------------
            m_resource_appender           =  l_res_result['info'].append

            for i, r in enumerate(resource, start=1):
                # Dict where store the results
                l_concrete_res  = {}

                # Resource to display
                l_concrete_res['main_info'] = getattr(r, self.MAIN_RESOURCES_PROPERTIES[l_resource.replace("RESOURCE_", "")])
                l_concrete_res['res_id']    = r.identity

                # Summary vulns
                l_concrete_res['vulns']    = self.__get_vulns_counter(r.associated_vulnerabilities)

                #
                # Display resource params
                #
                l_concrete_res['properties'] = self.__get_object_properties(r, self.PRIVATE_INFO_RESOURCES)


                #
                # Display the vulns
                #
                if r.associated_vulnerabilities:
                    l_assoc        = []
                    l_assoc_append = l_assoc.append
                    for l_res_vuln in r.associated_vulnerabilities:
                        if l_res_vuln.false_positive:
                            continue
                        l_assoc_res = {}
                        l_assoc_res['vuln_name']       = l_res_vuln.vulnerability_type
                        l_assoc_res['vuln_title']      = l_res_vuln.title
                        l_assoc_res['vuln_id']         = l_res_vuln.identity
                        l_assoc_res['vuln_properties'] = self.__get_object_properties(l_res_vuln, self.PRIVATE_INFO_VULN)

                        l_assoc_append(l_assoc_res)

                    l_concrete_res['associated_vulns'] = l_assoc

                m_resource_appender(l_concrete_res)



            # Add to the global results
            m_results_append(l_res_result)

        context['info_by_resource'] = m_results

    def fill_content_vuln(self, context):
        """
        Fill the context var with the "vulns" information.


        This method generates a list as format:

        >>>[
            {
               'vuln_name' : 'Name of vuln',

               'affected_resources':
               [
                   {
                       'resource_type': 'Type 1',
                       'main_info'    : 'http://www.info.com'
                   }
               ],

               'properties':
               [
                   {
                       'name'  : 'name of property',
                       'value' : 'value of property,
                   }
               ],

               'level': 'low'
            }
        ]

        :param context: Context var to fill.
        :type context: Context
        """

        m_results        = defaultdict(list)

        # Get all type of resources
        m_all_resources = set([x for x in dir(Resource) if x.startswith("RESOURCE")])

        for l_resource in m_all_resources:

            # Get resources URL resources
            resource = self.common_get_resources(Data.TYPE_RESOURCE, getattr(Resource, l_resource))

            if not resource:
                continue

            # Get the vulns of each resource
            for l_each_res in resource:
                for l_vuln in l_each_res.associated_vulnerabilities:
                    if l_vuln.false_positive:
                        continue
                    l_res_result = {}

                    # Get the vuln name using the class name
                    l_res_result['vuln_name']           = "%s : %s" % (l_vuln.vulnerability_type, l_vuln.title)

                    # Get the properties
                    l_res_result['properties']          = self.__get_object_properties(l_vuln, self.PRIVATE_INFO_VULN)

                    # Get associated resources with this vuln
                    l_res_affected        = []
                    l_res_affected_append = l_res_affected.append
                    for l_res in l_vuln.associated_resources:
                        l_info = {}
                        l_info['resource_type'] = l_res.__class__.__name__
                        l_info['main_info']     = getattr(l_res, self.MAIN_RESOURCES_PROPERTIES[l_res.__class__.__name__.upper()])

                        l_res_affected_append(l_info)

                    l_res_result['affected_resources']  = l_res_affected


                    m_results[l_vuln.display_name].append(l_res_result)

        context['info_by_vuln'] = dict(m_results)




    #----------------------------------------------------------------------
    def __get_vulns_counter(self, vuln):
        """
        Count the number of vulns of each type and return a list with the
        level of the vuln and the number of ocurrences.

        ..note:
           This function only return those levels that have more than 1
           ocurrences.

        :param vuln: List of vulnerabilities.
        :type vuln: list(Vulnerability)

        :return: a list as format: [{'low' : 1}, {'middle' : 2}]
        :rtype: list(dict())
        """

        m_counter                   = Counter()
        m_counter['critical']       = 0
        m_counter['high']           = 0
        m_counter['middle']         = 0
        m_counter['low']            = 0
        m_counter['informational']  = 0
        m_total                     = 0

        for l_v in vuln:
            if not l_v.false_positive:
                m_total += 1
                m_counter[l_v.level] +=1

        return [
            {'level' : k, 'number' : v}
            for k, v in m_counter.iteritems()
            if v > 0
        ]


    #----------------------------------------------------------------------
    def __get_non_trivial_properties(self, in_object, EXCLUDED_PARAMS=None):
        """
        Get an object and get their properties that are not private or are not
        in the EXCLUDED_PARAMS list an return a set with them.

        :param in_object: object instance.
        :type in_object: object.

        :param EXCLUDED_PARAMS: iterable with a list of parameters to ignore.
        :type EXCLUDED_PARAMS: Iterable

        :return: a set() with the object properties.
        :type: set
        """
        if in_object is None:
            raise ValueError("in_object can't be None")

        m_return = set()

        # Get all no trivial properties
        for x in dir(in_object):
            found = False

            # Looking for invalud param
            for y in EXCLUDED_PARAMS:
                if x.startswith("_") or x.startswith(y):
                    found = True
                    break

            if not found:
                m_return.add(x)

            found = False

        return m_return

    #----------------------------------------------------------------------
    def __get_object_properties(self, in_object, EXCLUDED_PARAMS):
        """
        Get an object a return a dict with their properties and values.

        :param in_object: object to get the properties.
        :type in_object: object instance.

        :param EXCLUDED_PARAMS: iterable with a list of parameters to ignore.
        :type EXCLUDED_PARAMS: Iterable

        :return: a list of dicts with the properties/values of the object as format: [{'prop1' : 'value1'}, {'prop2' : 'value2'}]
        :rtype: list(dict)
        """
        if in_object is None:
            raise ValueError("in_object can't be None")
        if EXCLUDED_PARAMS is None:
            raise ValueError("EXCLUDED_PARAMS can't be None")

        m_return        = []
        m_return_append = m_return.append

        for l_p in self.__get_non_trivial_properties(in_object, EXCLUDED_PARAMS):
            l_print_value = getattr(in_object, l_p)

            if l_print_value is not None:

                # String data
                if isinstance(l_print_value, basestring):
                    m_return_append({'name' : l_p.capitalize(), 'value' : getattr(in_object, l_p)})

                # Dict data
                if isinstance(l_print_value, dict) and len(l_print_value) > 0:
                    m_return_append({'name': l_p.capitalize(), 'value': "Dictionary"})

                # List data
                if isinstance(l_print_value, list) and len(l_print_value) > 0:
                    m_return_append({'name': l_p.capitalize(), 'value': "List"})

        return m_return
