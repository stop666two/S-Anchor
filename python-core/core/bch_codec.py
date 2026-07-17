import numpy as np

DATA_LEN = 7
ECC_LEN = 8
CODE_LEN = 15

# Primitive polynomial x^4 + x + 1
PRIMITIVE = 0b10011

# GF(16) tables
gf_exp = [0] * 16
gf_log = [0] * 16

gf_exp[0] = 1
for i in range(1, 15):
    gf_exp[i] = gf_exp[i - 1] << 1
    if gf_exp[i] & 0b10000:
        gf_exp[i] ^= PRIMITIVE
    gf_exp[i] &= 0b1111
gf_exp[15] = 1
for i in range(15):
    gf_log[gf_exp[i]] = i


def gf_mul(a: int, b: int) -> int:
    if a == 0 or b == 0:
        return 0
    return gf_exp[(gf_log[a] + gf_log[b]) % 15]


def gf_poly_mul(p1, p2):
    res = [0] * (len(p1) + len(p2) - 1)
    for i, c1 in enumerate(p1):
        for j, c2 in enumerate(p2):
            res[i + j] ^= gf_mul(c1, c2)
    return res


def gf_poly_eval(poly, x):
    result = poly[0]
    for i in range(1, len(poly)):
        result = gf_mul(result, x) ^ poly[i]
    return result


def make_generator():
    g = [1]
    for i in range(1, CORRECTABLE * 2 + 1):
        g = gf_poly_mul(g, [1, gf_exp[i]])
    return g


CORRECTABLE = 3
GENERATOR = make_generator()


def _poly_shift_left(poly, n):
    return poly + [0] * n


def encode(data_bits: np.ndarray) -> np.ndarray:
    assert len(data_bits) == DATA_LEN
    padded = list(data_bits) + [0] * ECC_LEN
    gen = GENERATOR[:]
    for i in range(DATA_LEN):
        if padded[i] != 0:
            shift = gen[:]
            shift = shift + [0] * (len(padded) - len(shift) - i) if len(shift) < len(padded) - i else shift[:len(padded) - i]
            for j in range(min(len(shift), len(padded) - i)):
                padded[i + j] ^= shift[j] if j < len(shift) else 0
    codeword = np.zeros(CODE_LEN, dtype=np.int8)
    codeword[:DATA_LEN] = data_bits
    codeword[DATA_LEN:] = padded[DATA_LEN:]
    return codeword


def decode(received: np.ndarray) -> np.ndarray:
    return received[:DATA_LEN]


def bits_to_bytes(bits: np.ndarray) -> bytes:
    result = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(min(8, len(bits) - i)):
            byte = (byte << 1) | int(bits[i + j])
        result.append(byte)
    return bytes(result)


def bytes_to_bits(data: bytes, n_bits: int) -> np.ndarray:
    bits = np.zeros(n_bits, dtype=np.int8)
    for i in range(n_bits):
        byte_idx = i // 8
        bit_idx = i % 8
        if byte_idx < len(data):
            bits[i] = (data[byte_idx] >> (7 - bit_idx)) & 1
    return bits
