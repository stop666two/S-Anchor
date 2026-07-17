import numpy as np

DATA_LEN = 7
ECC_LEN = 8
CODE_LEN = 15

# BCH(15,7,5) generator polynomial: x^8 + x^7 + x^6 + x^4 + 1
# Coefficients from x^8 down to x^0
GEN = [1, 1, 1, 0, 1, 0, 0, 0, 1]
GEN_DEG = 8

# GF(16) with primitive polynomial x^4 + x + 1
EXP = [0] * 16
LOG = [0] * 16
EXP[0] = 1
for i in range(1, 15):
    EXP[i] = EXP[i-1] << 1
    if EXP[i] & 0b10000:
        EXP[i] ^= 0b10011
    EXP[i] &= 0b1111
EXP[15] = 1
for i in range(15):
    LOG[EXP[i]] = i


def encode(data_bits: np.ndarray) -> np.ndarray:
    assert len(data_bits) == DATA_LEN
    m = list(data_bits) + [0] * ECC_LEN
    for i in range(DATA_LEN):
        if m[i]:
            for j in range(GEN_DEG + 1):
                m[i + j] ^= GEN[j]
    codeword = np.zeros(CODE_LEN, dtype=np.int8)
    codeword[:DATA_LEN] = data_bits
    codeword[DATA_LEN:] = m[DATA_LEN:]
    return codeword


def _eval_at(poly, alpha_pow):
    result = 0
    for c in poly:
        if result == 0:
            result = c
        else:
            if result and alpha_pow:
                result = EXP[(LOG[result] + alpha_pow) % 15]
            result ^= c
    return result


def _is_valid(codeword):
    alpha_pows = [1, 3]  # alpha^1 and alpha^3 are roots
    for ap in alpha_pows:
        val = _eval_at(list(codeword), ap)
        if val != 0:
            return False
    # Check S2, S4 (conjugates of S1)
    for ap in [2, 4, 6, 8, 12, 9]:
        val = _eval_at(list(codeword), ap)
        if val != 0:
            return False
    return True


def decode(received: np.ndarray) -> np.ndarray:
    if _is_valid(received):
        return received[:DATA_LEN]

    n = len(received)
    for i in range(n):
        t = received.copy(); t[i] ^= 1
        if _is_valid(t): return t[:DATA_LEN]

    for i in range(n):
        for j in range(i + 1, n):
            t = received.copy(); t[i] ^= 1; t[j] ^= 1
            if _is_valid(t): return t[:DATA_LEN]

    return received[:DATA_LEN]


def bits_to_bytes(bits: np.ndarray) -> bytes:
    r = bytearray()
    for i in range(0, len(bits), 8):
        b = 0
        for j in range(min(8, len(bits) - i)):
            b = (b << 1) | int(bits[i + j])
        r.append(b)
    return bytes(r)


def bytes_to_bits(data: bytes, n_bits: int) -> np.ndarray:
    bits = np.zeros(n_bits, dtype=np.int8)
    for i in range(n_bits):
        bi = i % 8
        if i // 8 < len(data):
            bits[i] = (data[i // 8] >> (7 - bi)) & 1
    return bits
