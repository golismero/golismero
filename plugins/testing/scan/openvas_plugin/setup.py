#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
GoLismero 2.0 - The web knife - Copyright (C) 2011-2014

Golismero project site: http://golismero-project.com
Golismero project mail: contact@golismero-project.com


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

from __future__ import print_function

import re
import os
import json
import argparse

from collections import namedtuple, defaultdict

try:
    import cPickle as Pickler
except ImportError:
    import pickle as Pickler

# Global regex
REGEX_PLUGIN_ID = re.compile(r'(?:SCRIPT_OID|script_[o]*id)[^\d]+(?:(?:\d+.){9})?(\d+)\'?\"?\)?(?:\s+)?;')

# Custom Types
RulePack = namedtuple("RulePack", ["rules", "rule_index"])
RuleComponent = namedtuple("RuleComponent",
                           [
                               "rule_id",
                               "comment",
                               "matching_types",
                               "filename_rules",
                               "content_rules",
                               "operator",
                               "rule_type"
                           ])

RuleGroup = namedtuple("RuleGroup", ["rules"])
Rule = namedtuple("Rule", ["regex", "group", "operator_next", "negate"])


#------------------------------------------------------------------------------
def get_nasl_files(path):
    """
    Get all .nasl files from a path

    :param path: Folder containing .nasl files.
    :type path: str

    :return: Iterator of file names.
    :rtype: iterator(str)
    """
    results = []
    results_append = results.append
    if path:
        for root, dirs, files in os.walk(path):
            for l_file in files:
                if l_file.endswith(".nasl"):
                    results_append(os.path.join(root, l_file))
    else:
        raise ValueError("Path can't be empty.")

    return results


#------------------------------------------------------------------------------
def rules_matcher(text, rules_group, rules_index, verbosity=0):
    """
    Rules matcher.

    Applies the rules group to the text and returns True if any rule matches.

    :param text: text where match the rules
    :param text: str

    :param rules_group: a RuleGroup.
    :type rules_group: RuleGroup

    :param rules_index: dict with rules grouped by type.
    :type rules_index: dict

    :param verbosity: Verbosity level. Used for debug.
    :type verbosity: int

    :return: True if match found. False otherwise.
    :rtype: bool
    """

    for rule_group in rules_group:
        last_matches = False
        for rule in rule_group.rules:

            rule_operator = rule.operator_next.lower()
            rule_regex = rule.regex
            rule_group = rule.group
            rule_negate = rule.negate

            # Apply regex
            if isinstance(rule_regex, basestring) or isinstance(rule_regex, unicode):
                m = rules_matcher(text, rules_index[rule_regex], rules_index)
            else:
                m = rule_regex.search(text)

            # Rule matches?
            if m:
                # If group is "*", not concrete group is needed -> Rules matches
                if rule_group == "*":
                    if rule_operator == "and":
                        last_matches = True
                        continue
                    else:
                        # Normal response is True
                        return False if rule_negate else True
                else:
                    if len(m.groups()) != int(rule_group):
                        # Normal response is False
                        return True if rule_negate else False
                    else:
                        if rule_operator == "and":
                            last_matches = True
                            continue
                        else:
                            # Normal response is True
                            return True if rule_negate else False
            else:
                # No match found.
                #
                # If operator is "or", wait for next rule to
                # determinate if rule is valid
                if rule_operator == "and":
                    # Normal response is False
                    return False if rule_negate is False else True

                if last_matches:
                    return True

    # If not found -> no rules that matches.
    return False


#------------------------------------------------------------------------------
def load_single_rule(rule):
    """
    This function loads a single rule from a dict and returns a Rule type.

    :param rule: dict with json information.
    :type rule: dict

    :return: Rule object.
    :rtype: Rule
    """

    _tmp_operator_title_file = rule.get("operator", u"or")
    _tmp_operator_title_file = _tmp_operator_title_file \
        if _tmp_operator_title_file != u"" and _tmp_operator_title_file is not None else u"or"

    try:
        _tmp_rule = re.compile(rule["regex"]) if not rule["regex"].startswith("REF://") \
            else rule["regex"].replace("REF://", "")
    except re.error, e:
        print("Error compiling regex '%s': %s" % (rule["regex"], e))
        exit(1)

    r = Rule(regex=_tmp_rule,
             group=rule.get("group", u"*"),
             operator_next=_tmp_operator_title_file,
             negate=bool(rule.get("negate", False)))

    return r


#------------------------------------------------------------------------------
def load_rules(rules_path):
    """
    Load the rules from json and convert into our custom format.

    :param rules_path: path or file that contains rules files.
    :type rules_path: str

    :return: A RulePack object
    :rtype: RulePack
    """
    rules_files = []

    if os.path.isdir(rules_path):
        for root, dirs, files in os.walk(rules_path):
            for l_file in files:
                if l_file.startswith("rules_") and l_file.endswith(".json"):
                    rules_files.append(os.path.join(root, l_file))
    else:
        rules_files.append(rules_path)

    # Load rules file
    all_rules = []
    for rule_file in rules_files:
        with open(rule_file, "rU") as f_in:
            all_rules.append(json.load(f_in))

    # Rule index
    rules_pack_index = defaultdict(list)

    # Rule list
    results_rules = []
    results_rules_append = results_rules.append

    # Parse and load rules
    for rules in all_rules:

        for rule_component in rules:
            #
            # Rules for file NAME
            in_filename_rules = []
            filename_rules = rule_component.get("filename_rules", "")
            filename_rules = filename_rules if filename_rules != u"" else []

            for rule_group in filename_rules:

                _tmp_rule_group = RuleGroup(rules=[load_single_rule(r) for r in rule_group])

                # Add rules to index by type
                rules_pack_index[rule_component["rule_type"]].append(_tmp_rule_group)

                in_filename_rules.append(_tmp_rule_group)

            #
            # Rules for file CONTENT
            in_content_rules = []
            file_content_rules = rule_component.get("content_rules", "")
            file_content_rules = file_content_rules if file_content_rules != u"" else []

            for rule_group in file_content_rules:
                _tmp_rule_group = RuleGroup(rules=[load_single_rule(r) for r in rule_group])

                # Add rules to index by type
                rules_pack_index[rule_component["rule_type"]].append(_tmp_rule_group)

                in_content_rules.append(_tmp_rule_group)

            #
            # Make the abstract type
            #
            _tmp_operator = rule_component.get("operator", "or")
            _tmp_operator = _tmp_operator if _tmp_operator != u"" and _tmp_operator is not None else "or"
            component = RuleComponent(rule_id=rule_component.get("rule_id", None),
                                      comment=rule_component.get("comment", ""),
                                      matching_types=rule_component["matching_types"],
                                      filename_rules=in_filename_rules,
                                      content_rules=in_content_rules,
                                      operator=_tmp_operator,
                                      rule_type=rule_component["rule_type"])
            results_rules_append(component)

    #
    # Unify all rules
    #
    pack = RulePack(rules=results_rules,
                    rule_index=rules_pack_index)

    return pack


#------------------------------------------------------------------------------
def get_script_id(text):
    """
    Get script ID from the text.

    :param text: text where looking for.
    :type text: str

    :return: script ID
    :type: int
    """
    r = REGEX_PLUGIN_ID.search(text)

    if r:
        if len(r.groups()) == 1:
            try:
                return int(r.group(1))
            except ValueError:
                raise ValueError("Incorrect regex to find ID in plugin.")


#------------------------------------------------------------------------------
def extract_info(path, rule_pack, display_processed=False, display_non_match=False, debug=False, verbosity=0):
    """
    Extract info from the plugins.

    :param path: plugins location.
    :type path: str

    :param rule_pack: RulePack object with rules to apply.
    :type rule_pack: RulePack

    :param display_non_match: display files that don't match with any rule.
    :type display_non_match: bool

    :param display_processed: display files that match with some rule.
    :type display_processed: bool

    :param debug: to enable debug.
    :type debug: bool

    :return: a dict with the resutls. Format: { "plugin_id": ([ "Class_type_1", "Class_type_2"], "RULE_TYPE") }
    :type: dict
    """

    # !!! Don't delete: This var was used for debug purposes and only enbled with "-d" option.
    plugins = [
        # "12planet_chat_server_xss.nasl",
        # "3com_nbx_voip_netset_detection.nasl",
        # "3com_switches.nasl",
        # "404_path_disclosure.nasl",
        # "4553.nasl",
        # "ubuntu_866_1.nasl",
        # "gb_ubuntu_USN_990_1.nasl",
        # "http_trace.nasl"
        # "freebsd_mod_php4-twig.nasl",
        # "sles9p5013929.nasl"
        # "gb_mssql_sp_replwritetovarbin_bof_vuln.nasl",
        #"gb_fedora_2007_3369_php-pear-MDB2-Driver-mysql_fc7.nasl",
        # "postgreSQL_multiple_security_vulnerabilities.nasl",
        # "postgresql_34069.nasl",
        # "gb_mysql_weak_passwords.nasl",
        # "mysql_37640.nasl",
        # "drupal_detect.nasl",
        "drupal_34779.nasl",
        # "sles9p5046302.nasl",
        # "sles9p5017417.nasl",
        # "sles9p5016079.nasl"
        # "gb_fedora_2012_9324_mysql_fc16.nasl"
    ]

    # Load all plugin list
    if debug:
        plugin_list = []
        for p in plugins:
            plugin_list.append(os.path.join(path, p))
    else:
        plugin_list = get_nasl_files(path)
    plugin_count = len(plugin_list)

    results = {}
    results_update = results.update

    # For testing
    files = {}
    not_processed = {}

    #
    # Find in plugins
    #
    for i in xrange(plugin_count):

        # Get next plugin to process
        f = plugin_list[i]

        # Read file
        with open(f, "rU") as f_in:
            file_content = f_in.read()

        plugin_id = get_script_id(file_content)

        found = False
        # Apply each Rule component to the plugin
        for config_rules in rule_pack.rules:
            rule_type = config_rules.rule_type

            #
            # 1º - Looking for un file name
            #
            if rules_matcher(os.path.split(f)[1], config_rules.filename_rules, rule_pack.rule_index, verbosity):
                results_update({int(plugin_id): (config_rules.matching_types, rule_type)})
                found = True
                files[plugin_id] = f

            # Is enough with the title matching?
            if found and config_rules.operator == u"or":
                break

            #
            # 2º - Looking for in file content
            #
            if rules_matcher(file_content, config_rules.content_rules, rule_pack.rule_index, verbosity):
                results_update({int(plugin_id): (config_rules.matching_types, rule_type)})
                found = True
                files[plugin_id] = f
                break

        # If not match found, add to not found list.
        if found is False:
            not_processed[plugin_id] = f

    #
    # !!! Don't delete. Used for debug
    #
    # Display only for debug
    if display_non_match:
        print("Non processed files:")
        for i, v in not_processed.iteritems():
            print("%s\t%s" % (i, v))

        print("\n\nTotal non processed files: %s" % len(not_processed))

    # Display only for debug
    if display_processed:
        print("\n\n[*] Processed files:")
        for i, v in results.iteritems():
            print("%s: " % i)
            print("   - %s (%s)" % (v[0], v[1]))
            print("   - %s" % files[i])

    print("\n\nTotal processed: %s" % len(results))

    return results


#------------------------------------------------------------------------------
def main(args):
    """
    Main function.

    :param args: Arg parser arguments from command line.
    """
    path_openvas_plugins = args.OPENVAS_PLUGINS
    path_out = args.OUTPUT_BBDD
    debug = args.DEBUG
    verbosity = args.VERBOSE
    rules_file = args.RULES
    display_processed = args.DISPLAY_PROCESSED
    display_non_match = args.DISPLAY_NOT_MATCH

    if not os.path.isdir(path_out):
        print("\n[!] Output database must be a folder, not a file.\n")
        exit(1)

    # Add filename to de database
    path_out = os.path.join(args.OUTPUT_BBDD, "openvas.db")

    # Load rules
    if rules_file:
        rule_pack = load_rules(rules_file)
    else:
        rule_pack = load_rules(os.getcwd())

    # Extract info form the plugins
    info = extract_info(path_openvas_plugins, rule_pack, display_processed, display_non_match, debug, verbosity)

    # Store in database
    Pickler.dump(info, open(path_out, 'wb'), 2)


#------------------------------------------------------------------------------
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Generates OpenVAS database.')
    parser.add_argument('-o', dest="OUTPUT_BBDD", help="output database folder.",  # Current directory default
                        default=os.path.abspath(os.path.split(__file__)[0]))
    parser.add_argument('-p', dest="OPENVAS_PLUGINS", help="openvas plugins path", required=True)
    parser.add_argument('-v', action="count", dest="VERBOSE", help="increases debug level", default=0)
    parser.add_argument('-d', action="store_true", dest="DEBUG", help="enable debug mode", default=False)
    parser.add_argument('--rules', dest="RULES", help="load only a concrete file rules", default=None)
    parser.add_argument('--display-processed', action="store_true", dest="DISPLAY_PROCESSED",
                        help="display all processed files", default=False)
    parser.add_argument('--display-non-match', action="store_true", dest="DISPLAY_NOT_MATCH",
                        help="display files that don't match with any rule", default=False)

    args = parser.parse_args()

    main(args)
