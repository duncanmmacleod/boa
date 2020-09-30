# convert between recipe.yaml and meta.yaml
import ruamel
from ruamel.yaml.representer import RoundTripRepresenter
from ruamel.yaml.comments import CommentedMap
from ruamel.yaml import YAML
from collections import OrderedDict
from pprint import pprint
import collections
import os
import sys
import re

class MyRepresenter(RoundTripRepresenter):
    pass
ruamel.yaml.add_representer(OrderedDict, MyRepresenter.represent_dict, representer=MyRepresenter)


def main(docname):

    with open(docname, 'r') as fi:
        lines = fi.readlines()
    context = {}
    rest_lines = []
    for line in lines:
        # print(line)
        if '{%' in line:
            set_expr = re.search('{%(.*)%}', line)
            set_expr = set_expr.group(1)
            set_expr = set_expr.replace('set', '', 1).strip()
            exec(set_expr, globals(), context)
        else:
            rest_lines.append(line)

    yaml = YAML(typ='rt')
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    yaml.indent(sequence=4, offset=2)
    yaml.width = 1000
    yaml.Representer = MyRepresenter
    yaml.Loader = ruamel.yaml.RoundTripLoader

    result_yaml = CommentedMap()
    result_yaml['context'] = context

    def has_selector(s):
        return s.strip().endswith(']')

    quoted_lines = []
    for line in rest_lines:
        if has_selector(line):
            selector_start = line.rfind('[')
            selector_end = line.rfind(']')
            selector_content = line[selector_start + 1:selector_end]

            if line.strip().startswith('-'):
                line = line[:line.find('-') + 1] + f' sel({selector_content}): ' + line[line.find('-') + 1:min(line.rfind('#'), line.rfind('['))].strip() + '\n'
        quoted_lines.append(line)
    rest_lines = quoted_lines


    def check_if_quoted(s):
        s = s.strip()
        return (s.startswith('"') or s.startswith("'"))

    quoted_lines = []
    for line in rest_lines:
        if '{{' in line:
            # make sure that jinja stuff is quoted
            if line.find(':') != -1:
                idx = line.find(':')
            elif line.strip().startswith('-'):
                idx = line.find('-')
            rest = line[idx + 1:]

            if not check_if_quoted(rest):
                if '\'' in rest:
                    rest = rest.replace('\'', '\"')

                line = line[:idx + 1] + f" \'{rest.strip()}\'\n"
        quoted_lines.append(line)
    rest_lines = quoted_lines

    skips, wo_skip_lines = [], []
    for idx, line in enumerate(rest_lines):
        if line.strip().startswith('skip'):
            parts = line.split(':')
            rhs = parts[1].strip()
            if rhs.startswith('true'):
                selector_start = line.rfind('[')
                selector_end = line.rfind(']')
                selector_content = line[selector_start + 1:selector_end]
                skips.append(selector_content)
            else:
                print("ATTENTION skip: false not handled!")
        else:
            wo_skip_lines.append(line)

    rest_lines = wo_skip_lines
    result_yaml.update(ruamel.yaml.load(''.join(rest_lines), ruamel.yaml.RoundTripLoader))

    if len(skips) != 0:
        result_yaml['build']['skip'] = skips

    new_outputs = {}
    if result_yaml.get('outputs'):
        for o in result_yaml['outputs']:
            name = o['name']
            package = {
                'name': name
            }
            del o['name']
            if o.get('version'):
                package['version'] = o['version']
                del o['version']

            build = {}
            if o.get('script'):
                build['script'] = o['script']
                del o['script']

            o['package'] = package
            o['build'] = build

    from io import StringIO
    output = StringIO()
    yaml.dump(result_yaml, output)

    # Hacky way to insert an empty line after the context-key-object
    context_output = StringIO()
    yaml.dump(context, context_output)
    context_output = context_output.getvalue()
    context_output_len = len(context_output.split('\n'))

    final_result = output.getvalue()
    final_result_lines = final_result.split('\n')
    final_result_lines.insert(context_output_len, '')

    print('\n'.join(final_result_lines))