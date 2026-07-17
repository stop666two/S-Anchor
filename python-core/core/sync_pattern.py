import numpy as np

SYNC_LEN = 64


def generate_sync_pattern(seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, size=SYNC_LEN, dtype=np.int8)


def correlate_sync(received: np.ndarray, sync: np.ndarray) -> int:
    sync_normalized = 2 * sync.astype(np.float64) - 1
    best_offset = -1
    best_corr = -1.0
    for offset in range(len(received) - len(sync) + 1):
        segment = received[offset:offset + len(sync)]
        seg_normalized = 2 * segment.astype(np.float64) - 1
        corr = np.dot(seg_normalized, sync_normalized) / len(sync)
        if corr > best_corr:
            best_corr = corr
            best_offset = offset
    return best_offset, best_corr


def build_payload(sync: np.ndarray, data_bits: np.ndarray) -> np.ndarray:
    return np.concatenate([sync, data_bits])
