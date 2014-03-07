# How to use OpenVAS correlation

To use OpenVAS correlation you must setup the plugin first. Follow these steps:

## 1 - Download OpenVAS plugins

You need the OpenVAS plugins feed. You can download it from [http://www.openvas.org/openvas-nvt-feed-current.tar.bz2](http://www.openvas.org/openvas-nvt-feed-current.tar.bz2) or get it from your OpenVAS installation.

## 2 - Generate database

Now we need to generate the database. To do that, you must run:

```python setup.py -p YOUR_PLUGIN_LOCATION -v```

## 3 - Done

Now we have a pickled database called: **openvas.db**

# How does it work?

OpenVAS generator produces a rules file. This file contains the expressions to find and correlate OpenVAS plugins with the GoLismero data model.

The setup.py script will search in the specified directory and load all files called "rules_*json", containing the rules.

# Available types of vulnerabilities

Each vulnerability has its type, in order to be classified by the OpenVAS plugin. Available types are:

 * platform
 * software
 * webapp
 * malware
 * http

# Rules format

## Rules file format

Rule files have the following JSON format:

 * comment: A comment about the rule.
 * rule_id: Unique identification of the rule.
 * rule_type: Category of the rule (one of the types listed above).
 * matching_types: Classes types, in GoLismero data model, that matches with this rule.
 * filename_rules: Rules applied to the file name only.
 * content_rules: Rules applied to the file content only.

## Rule details

Each rule (in section filename_rules and content_rules) has this format:

### Structure:

 * Each section is formed by a group of rules and can have more than one group.
 * Each group can have more han one rule.

### Rule specification:

Each rule has 3 parameters: 

 * regex: String. Defines how the rule is matched. The value can be:
   * Regular expression: Rule will match if this regex matches.
   * Reference: If a reference is specified instead, the rule matches if the reference matches with all "rules_types" or a concrete "rule_id". References start with the prefix: "REF://".
 * group: Integer or "\*". A regex can have more than one group. The rule matches if the regex has this number of groups. If "\*" is specified, any number of groups will match.
 * operator: Boolean operator. Specify the relation to the next rule (in rule group). Allowed operators are:
   * or: If this rule matches, the rule group is accepted. If not, it try to match the next rule. Default value if not specified.
   * and: If this rule matches, try to match the next rule. If not, the rule group is not accepted.
 * negate: Boolean. If set to "true", the above logic for accepting the rule is inverted.
