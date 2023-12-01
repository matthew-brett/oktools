""" Test parsetests
"""

from oktools import parsetests as otp

import pytest


EG_CELL_TEXT = """\
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


def test_parse_header():
    assert otp.parse_header('#t q2bi_extended') == {
        'name': 'q2bi_extended',
        'points': 1,
        'suites': []}
    assert otp.parse_header('#t q2bi_extended points=1') == {
        'name': 'q2bi_extended',
        'points': 1,
        'suites': []}
    assert otp.parse_header('#t q2bi_extended points=5') == {
        'name': 'q2bi_extended',
        'points': 5,
        'suites': []}


def test_parse_params():
    assert otp.parse_marked('#t foo=.1', '#t') == dict(foo=.1)
    assert otp.parse_marked('#b foo=.1', '#b') == dict(foo=.1)
    with pytest.raises(otp.HeaderParserError):
        otp.parse_marked('#t foo=.1', '#b')
    assert otp.parse_marked('#t  bar=baz', '#t') == dict(bar='baz')
    assert otp.parse_marked('#t  bar=baz', '#t') == dict(bar='baz')
    assert otp.parse_marked('#t  bar=True', '#t') == dict(bar=True)
    assert otp.parse_marked('#t  bar=False', '#t') == dict(bar=False)
    assert otp.parse_marked('#t  bar="baz boo"', '#t') == dict(bar='baz boo')
    assert otp.parse_marked("#t  bar='baz boo'", '#t') == dict(bar='baz boo')
    assert (otp.parse_marked("#t  bar_buv='baz boo'", '#t') ==
            dict(bar_buv='baz boo'))
    assert (otp.parse_marked('#t foo=.1 bar=baz', '#t') ==
            dict(foo=.1, bar='baz'))
    with pytest.raises(otp.HeaderParserError):
        otp.parse_marked('# A comment', '#A')
    with pytest.raises(otp.HeaderParserError):
        otp.parse_marked('#t A comment', '#t')
    with pytest.raises(otp.HeaderParserError):
        otp.parse_marked('#t bar=', '#t')
    with pytest.raises(otp.HeaderParserError):
        otp.parse_marked('#t bar=baz buv', '#t')


def test_to_doctest():
    assert otp.to_doctest('foo') == '>>> foo'
    assert otp.to_doctest('foo\nbar') == '>>> foo\n>>> bar'
    assert otp.to_doctest('foo\nbar') == '>>> foo\n>>> bar'
    assert (otp.to_doctest('if a == 1:\n    b = 2\n    print(a + b)\nc = 3') ==
            '>>> if a == 1:\n...     b = 2\n...     print(a + b)\n>>> c = 3')
    in_code = r'''
def func(a):
    b = 3
    return a + b

if func(-3):
    print('yes')
'''
    out_code = r'''>>>
>>> def func(a):
...     b = 3
...     return a + b
>>>
>>> if func(-3):
...     print('yes')'''
    actual = otp.to_doctest(in_code)
    assert actual == out_code
    in_code = """
a = 1
# Comment
# Comment 2

# Comment 3
if a == 1:
    b = 3
    print(a)
print('Done')
"""
    out_code = '''>>>
>>> a = 1
>>> # Comment
>>> # Comment 2
>>>
>>> # Comment 3
>>> if a == 1:
...     b = 3
...     print(a)
>>> print('Done')'''
    actual = otp.to_doctest(in_code)
    assert actual == out_code


def test_test_parse():
    actual = otp.parse_test(EG_CELL_TEXT)
    assert actual == EG_CELL_OUT
