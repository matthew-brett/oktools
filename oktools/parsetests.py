""" Parse test cells in notebooks

Test blocks are code cells in notebooks, of this form::

    #t q1a_2 points=1
    # a should be greater than 0.
    assert a > 0
    #c
    # a should be less than 10.
    assert a < 10
    #s private=true
    # a should be equal to 1.
    assert a == 1
    #c
    #t# Comment not visible in output test.
    # a should be less than 5.
    assert a == 1

This defines a single test named ``q1a_2`, worth 1 point.  There are 4 cases in
2 suites.  The second suite is marked as private.

The test (``#t``) name must be specified after the ``#t`` marker; the default
points value is 1.  In the example above, we could have omitted ``points=1`` to
get the same outcome, as 1 is the default.

* ``#s`` lines mark the start of a new suite in the current test.
* ``#c`` lines mark the start of a new case in the current suite.

All of ``#t, #s`` and ``#c`` lines can continue with key=value parameter lists
(although the ``#t`` marker should also have a name parameter preceding).
"""

import re
from copy import deepcopy
from pathlib import Path
from pprint import pformat
from argparse import ArgumentParser, RawDescriptionHelpFormatter

import jupytext


class HeaderParserError(Exception):
    """ Error for header parsing """


NAME_VALUE_RE = re.compile(
    r'''\s*  # Keep track of preceeding space.
    (?P<name>\w+)\s*=\s*   # name=
    ( # followed by one or more of
    (?P<dqstring>".*?") |  # double-quoted string
    (?P<sqstring>'.*?') |  # single-quoted string
    # This from https://stackoverflow.com/a/12643073/1939576
    (?P<number>[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)) |
    (?P<boolean>[Tt]rue|[Ff]alse) | # bool
    (?P<uqstring>\w+)  # unquoted string.
    )\s*  # and suffixed space.
    ''',
    flags=re.VERBOSE)


# Processing functions for all above match types.
_val_procs = dict(
    dqstring=lambda v : v[1:-1],
    sqstring=lambda v : v[1:-1],
    number=lambda x : float(x) if '.' in x else int(x),
    boolean=lambda x : x.lower() == 'true',
    uqstring=str
)

def proc_param(m):
    d = m.groupdict()
    name = d.pop('name')
    values = [v for v in d.values() if v]
    if len(values) != 1:
        raise HeaderParserError(f'Unexpected number of values in {m.group()}')
    for k, v in d.items():
        if v:
            return name, _val_procs[k](v)
    raise HeaderParserError(f'Unexpected parameter in {m.group()}')


HEADER_RE = re.compile(r'^#t\s+(\w+)(\s+.*?)?$')


def parse_header(line):
    if not (m := HEADER_RE.match(line)):
        return None
    name, param_str = m.groups()
    return ({'points': 1} |
            (get_params(param_str) if param_str else {}) |
            {'name': name, 'suites': []})


def parse_marked(line, marker):
    if not line.startswith(marker):
        raise HeaderParserError(f'Expecting {marker} at start of line')
    return get_params(line[len(marker):].strip())


def get_params(param_str):
    param_str = param_str.strip()
    if param_str == '':
        return {}
    matches = [m for m in NAME_VALUE_RE.finditer(param_str)]
    if not ''.join(m.group() for m in matches) == param_str:
        raise HeaderParserError(f'Unexpected text in {param_str}')
    return dict([proc_param(m) for m in matches])


PARTS = {
    'suite': {'default': {
        'cases': [],
        'scored': True,
        'setup': '',
        'teardown': '',
        'type': 'doctest'},
        'marker': '#s'},
    'case': {'default': {
        'code': None,
        'hidden': False,
        'locked': False},
        'marker': '#c'}
}


COMMENT_MARKER = '#t#'


def get_part(lines, name):
    info = PARTS[name]
    part = deepcopy(info['default'])
    if lines and lines[0].startswith(info['marker']):
        line = lines.pop(0)
        part = part | parse_marked(line, info['marker'])
        return part, True
    return part, False


def parse_test(text):
    lines = text.strip().splitlines()
    if not lines:
        return None
    test = parse_header(lines.pop(0))
    if not test:
        return None
    suite = None
    while True:
        new_suite, parsed = get_part(lines, 'suite')
        if suite is None or parsed:  # Start new suite if suite line.
            suite = new_suite
            test['suites'].append(suite)
            case = None
        new_case, parsed = get_part(lines, 'case')
        if case is None or parsed:  # Start new case if case line.
            case = new_case
            suite['cases'].append(case)
        try:
            line = lines.pop(0)
        except IndexError:
            break
        # Remaining lines are comments or code lines
        if not line.startswith(COMMENT_MARKER):
            case['code'] = (line if case['code'] is None
                            else case['code'] + '\n' + line)
    return test


def to_doctest(code):
    return '>>> ' + '\n>>> '.join(code.splitlines())


def cases2doctest(test):
    out = deepcopy(test)
    for suite in out['suites']:
        for case in suite['cases']:
            case['code'] = to_doctest(case['code'])
    return out


def get_parser():
    parser = ArgumentParser(description=__doc__,  # Usage from docstring
                            formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('nb_fname',
                        help='Notebook filename')
    parser.add_argument('-p', '--private', action='store_true',
                        help='Include private tests')
    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    nb_path = Path(args.nb_fname)
    nb = jupytext.read(nb_path)
    tests_path = nb_path.parent / 'tests'
    for cell in nb['cells']:
        if cell['cell_type'] != 'code':
            continue
        if not (test := parse_test(cell['source'])):
            continue
        if not args.private:
            test['suites'] = [s for s in test['suites'] if not s.get('private')]
        out_path = tests_path / f"{test['name']}__.py"
        test_text = pformat(cases2doctest(test))
        out_path.write_text('tests = ' + test_text)
