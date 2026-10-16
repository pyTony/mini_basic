import pytest
from mini_basic.util.basic_errors import basic_error_wording

@pytest.mark.parametrize('message,expected', [
    # Illegal function call
    ("float() argument must be a string or a number, not 'complex'", 'illegal function call'),
    ('math domain error', 'illegal function call'),
    ('expected a nonnegative input', 'illegal function call'),
    ('expected a positive input', 'illegal function call'),

    # Type mismatch
    ('could not convert string to float: "abc"', 'type mismatch'),
    ('must be real number, not str', 'type mismatch'),
    ("unsupported operand type(s) for +: 'int' and 'str'", 'type mismatch'),
    ('can only concatenate str (not "int") to str', 'type mismatch'),
    ("can't multiply sequence by non-int of type 'str'", 'type mismatch'),
    ("bad operand type for unary -: 'str'", 'type mismatch'),
    ("'int' object is not callable", 'type mismatch'),
    ("'int' object is not subscriptable", 'type mismatch'),

    # Syntax error
    ('was never closed', 'syntax error'),
    ('unmatched )', 'syntax error'),
    ('unexpected EOF while parsing', 'syntax error'),
    ("'int' object is not iterable", 'syntax error'),
    ("'int' object is not a container or iterable", 'syntax error'),
    ('unterminated string literal', 'syntax error'),

    # Division by zero
    ('division by zero', 'division by zero'),
    ('float division by zero', 'division by zero'),
    ('integer division or modulo by zero', 'division by zero'),
    ('float modulo by zero', 'division by zero'),

    # Overflow
    ('Result too large', 'overflow'),
    ('math range error', 'overflow'),
    ('int too large to convert to float', 'overflow'),
    ('Numerical result out of range', 'overflow'),

    # Unmatched
    ('some other error message', 'some other error message'),
    ('ValueError: something wrong', 'ValueError: something wrong'),

    # Locus stripping
    ('math domain error (<string>, line 10)', 'illegal function call'),
    ('unsupported operand type (<string>, line 42)', 'type mismatch'),
    ('unmatched ) (<string>, line 1)', 'syntax error'),
    ('division by zero (<string>, line 999)', 'division by zero'),
    ('Result too large (<string>, line 0)', 'overflow'),
    ('some other error (<string>, line 5)', 'some other error'),
])
def test_basic_error_wording(message, expected):
    assert basic_error_wording(message) == expected

def test_basic_error_wording_strips_locus_even_if_no_match():
    # specifically test the locus stripping
    assert basic_error_wording("unknown error (<string>, line 5)") == "unknown error"
    assert basic_error_wording(" (<string>, line 123) leading space") == "leading space"
