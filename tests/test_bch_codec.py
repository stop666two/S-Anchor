import numpy as np
from core.bch_codec import encode, decode, bytes_to_bits, bits_to_bytes, DATA_LEN, CODE_LEN


def test_bch_roundtrip():
    data = np.array([1, 0, 1, 0, 1, 0, 1], dtype=np.int8)
    codeword = encode(data)
    assert len(codeword) == CODE_LEN
    decoded = decode(codeword)
    np.testing.assert_array_equal(decoded, data)


def test_bch_single_bit_error():
    data = np.array([1, 0, 1, 0, 1, 0, 1], dtype=np.int8)
    codeword = encode(data)
    corrupted = codeword.copy()
    corrupted[3] ^= 1
    decoded = decode(corrupted)
    np.testing.assert_array_equal(decoded, data)


def test_bch_double_bit_error():
    data = np.array([1, 0, 1, 0, 1, 0, 1], dtype=np.int8)
    codeword = encode(data)
    corrupted = codeword.copy()
    corrupted[3] ^= 1
    corrupted[7] ^= 1
    decoded = decode(corrupted)
    np.testing.assert_array_equal(decoded, data)


def test_bytes_to_bits():
    data = b'\xAA'
    bits = bytes_to_bits(data, 8)
    expected = np.array([1, 0, 1, 0, 1, 0, 1, 0], dtype=np.int8)
    np.testing.assert_array_equal(bits, expected)


def test_bits_to_bytes():
    bits = np.array([1, 0, 1, 0, 1, 0, 1, 0], dtype=np.int8)
    result = bits_to_bytes(bits)
    assert result == b'\xAA'
