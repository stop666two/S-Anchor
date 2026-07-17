import numpy as np


def embed_bit(svd_u: np.ndarray, svd_s: np.ndarray, svd_vt: np.ndarray, bit: int, delta: float) -> np.ndarray:
    s_max = svd_s[0]
    q = s_max / delta
    r = q - np.floor(q)
    if bit == 1:
        if r < 0.25 or r >= 0.75:
            s_max_modified = (np.floor(q) + 0.5) * delta
        else:
            s_max_modified = s_max
    else:
        if 0.25 <= r < 0.75:
            s_max_modified = (np.floor(q)) * delta
        else:
            s_max_modified = s_max
    svd_s[0] = s_max_modified
    modified = svd_u @ np.diag(svd_s) @ svd_vt
    return modified


def extract_bit(svd_s: np.ndarray, delta: float) -> int:
    s_max = svd_s[0]
    q = s_max / delta
    r = q - np.floor(q)
    if r < 0.25 or r >= 0.75:
        return 0
    else:
        return 1


def embed_bits_in_blocks(dct_blocks: np.ndarray, bits: np.ndarray, delta: float, sync_len: int) -> np.ndarray:
    n_blocks = dct_blocks.shape[0]
    n_bits = len(bits)
    assert n_blocks >= n_bits, f"Not enough blocks ({n_blocks}) for {n_bits} bits"

    modified = dct_blocks.copy()

    for i in range(n_bits):
        mid_freq = modified[i, 2:6, 2:6]
        u, s, vt = np.linalg.svd(mid_freq, full_matrices=False)
        mid_freq_modified = embed_bit(u, s, vt, bits[i], delta)
        modified[i, 2:6, 2:6] = mid_freq_modified

    return modified


def extract_bits_from_blocks(dct_blocks: np.ndarray, delta: float, n_bits: int) -> np.ndarray:
    bits = np.zeros(n_bits, dtype=np.int8)
    for i in range(n_bits):
        mid_freq = dct_blocks[i, 2:6, 2:6]
        _, s, _ = np.linalg.svd(mid_freq, full_matrices=False)
        bits[i] = extract_bit(s, delta)
    return bits
