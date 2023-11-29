""" Parse test cells in notebooks

Test blocks are code cells in notebooks, of this form::

    #t name=q1a_2 points=1
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

This defines a single test named ``q1a_2`, work 1 point.  There are 4 cases of
which the last two are private.

Names and points are only valid in the first ``#t`` definition line.
Specifically, later ``#t`` cannot override the name or points.  The name must
be specified; the default points value is 1.  In the example above, we could
have omitted ``points=1`` to get the same outcome, as 1 is the default.

Parameters set in ``#t`` lines hold until overridden by later ``#t`` lines.
Hence the last _two_ tests are private.
"""

import re
from copy import deepcopy


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


def int_or_float(v):
    if '.' in v:
        return float(v)
    return int(v)


_val_procs = dict(
    dqstring=lambda v : v[1:-1],
    sqstring=lambda v : v[1:-1],
    number=int_or_float,
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


def parse_t(line, test_marker):
    if not line.startswith(test_marker):
        raise HeaderParserError(f'Expecting {test_marker} at start of line')
    param_str = line[len(test_marker):].strip()
    if param_str == '':
        return {}
    matches = [m for m in NAME_VALUE_RE.finditer(param_str)]
    if not ''.join(m.group() for m in matches) == param_str:
        raise HeaderParserError(f'Unexpected text in {param_str}')
    return dict([proc_param(m) for m in matches])


PARTS = {
    'test': {'default': {
        'name': None,
        'points': 1,
        'suites': []},
        'marker': '#t',
    },
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
        part = part | parse_t(line, info['marker'])
        return part, True
    return part, False


def parse_test(text):
    lines = [L for L in text.strip().splitlines()
             if not L.startswith(COMMENT_MARKER)]
    test, parsed = get_part(lines, 'test')
    if not parsed:
        return None
    suite = None
    while True:
        new_suite, parsed = get_part(lines, 'suite')
        if suite is None or parsed:  # Start new suite if suite line.
            suite = new_suite
            test['suites'].append(suite)
            print('Starting new suite')
            case = None
        new_case, parsed = get_part(lines, 'case')
        if case is None or parsed:  # Start new case if case line.
            case = new_case
            suite['cases'].append(case)
            print('Starting new case')
        if not lines:
            break
        # Remaining lines are code lines
        line = lines.pop(0)
        print(f'Line is: "{line}"')
        case['code'] = (line if case['code'] is None
                        else case['code'] + '\n' + line)
        print('case code is:\n', case['code'], '\n---')
    return test
