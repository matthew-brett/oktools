""" Test parsetests
"""

from oktools import parsetests as otp

import pytest


EG_CELL_TEXT = """\
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
"""

EG_CELL_OUT = {
    'name': 'q1a_2',
    'points': 1,
    'suites': [
        {'cases': [
            {'code': '''\
# a should be greater than 0.
assert a > 0''',
             'hidden': False,
             'locked': False},
            {'code': '''\
# a should be less than 10.
assert a < 10''',
             'hidden': False,
             'locked': False}],
            'scored': True,
            'setup': '',
            'teardown': '',
            'type': 'doctest'
        },
        {'cases': [
            {'code': '''\
# a should be equal to 1.
assert a == 1''',
             'hidden': False,
             'locked': False},
            {'code': '''\
# a should be less than 5.
assert a == 1''',
             'hidden': False,
             'locked': False},
        ],  # End of cases
            'private': True,
            'scored': True,
            'setup': '',
            'teardown': '',
            'type': 'doctest'
        },  # End of suite
    ]  # End of suites.
}


def test_header_parse():
    assert otp.parse_t('#t foo=.1', '#t') == dict(foo=.1)
    assert otp.parse_t('#b foo=.1', '#b') == dict(foo=.1)
    with pytest.raises(otp.HeaderParserError):
        otp.parse_t('#t foo=.1', '#b')
    assert otp.parse_t('#t  bar=baz', '#t') == dict(bar='baz')
    assert otp.parse_t('#t  bar=baz', '#t') == dict(bar='baz')
    assert otp.parse_t('#t  bar=True', '#t') == dict(bar=True)
    assert otp.parse_t('#t  bar=False', '#t') == dict(bar=False)
    assert otp.parse_t('#t  bar="baz boo"', '#t') == dict(bar='baz boo')
    assert otp.parse_t("#t  bar='baz boo'", '#t') == dict(bar='baz boo')
    assert (otp.parse_t("#t  bar_buv='baz boo'", '#t') ==
            dict(bar_buv='baz boo'))
    assert otp.parse_t('#t foo=.1 bar=baz', '#t') == dict(foo=.1, bar='baz')
    with pytest.raises(otp.HeaderParserError):
        otp.parse_t('# A comment', '#A')
    with pytest.raises(otp.HeaderParserError):
        otp.parse_t('#t A comment', '#t')
    with pytest.raises(otp.HeaderParserError):
        otp.parse_t('#t bar=', '#t')
    with pytest.raises(otp.HeaderParserError):
        otp.parse_t('#t bar=baz buv', '#t')


def test_test_parse():
    actual = otp.parse_test(EG_CELL_TEXT)
    assert actual == EG_CELL_OUT