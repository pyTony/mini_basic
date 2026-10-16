import pytest
from mini_basic.bbc_detokenize import detect_bbc_binary_format

def test_detect_bbc_binary_format():
    """Test detect_bbc_binary_format correctly identifies formats and returns None for unknown/invalid ones."""

    # Test case for `len(data) < 4`
    assert detect_bbc_binary_format(b'123') is None
    assert detect_bbc_binary_format(b'') is None

    # Test case for `tail == b'\r\x00\xff\xff'` -> russell
    assert detect_bbc_binary_format(b'dummy\r\x00\xff\xff') == 'russell'
    assert detect_bbc_binary_format(b'\r\x00\xff\xff') == 'russell'

    # Test case for `if len(data) >= 2 and data[-2:] == b'\r\xff': return 'wilson'`
    assert detect_bbc_binary_format(b'some_data\r\xff') == 'wilson'
    assert detect_bbc_binary_format(b'xy\r\xff') == 'wilson'

    # Test case for `if data[0] == 0x0D and len(data) >= 6 and data[-1] == 0xFF:`
    assert detect_bbc_binary_format(b'\x0D1234\x00\xFF') == 'wilson'
    assert detect_bbc_binary_format(b'\x0D123456\x00\xFF') == 'wilson'

    # Test cases that return None at the end
    assert detect_bbc_binary_format(b'some_random_data_without_tail') is None
    assert detect_bbc_binary_format(b'\x0D123\x00') is None # Misses `data[-1] == 0xFF`
    assert detect_bbc_binary_format(b'\x0C1234\xFF') is None # Misses `data[0] == 0x0D`
    assert detect_bbc_binary_format(b'\x0D12\xFF') is None # length 4 < 6, so `len(data) >= 6` fails
