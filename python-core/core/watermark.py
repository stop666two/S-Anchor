import numpy as np
from PIL import Image

from .config import WatermarkConfig
from .dwt import get_full_coeffs, reconstruct_from_ll
from .dct import dct_blockwise, idct_blockwise
from .svd_qim import embed_bits_in_blocks, extract_bits_from_blocks
from .sync_pattern import generate_sync_pattern, correlate_sync, build_payload, SYNC_LEN
from .bch_codec import encode as bch_encode, decode as bch_decode, bytes_to_bits, bits_to_bytes, DATA_LEN
from .metrics import psnr, ssim


def _calc_payload(data: bytes, config: WatermarkConfig, max_bits: int) -> np.ndarray:
    sync = generate_sync_pattern(config.sync_seed) if config.sync_enabled else np.array([], dtype=np.int8)
    avail = max_bits - len(sync)
    if avail <= 0:
        raise ValueError(f"Not enough capacity: need {len(sync)} for sync, only {max_bits} blocks")

    n_data = min(len(data) * 8, avail)
    if n_data < 8:
        raise ValueError(f"Not enough capacity: image too small ({avail} bits available)")

    data = data[:max(1, n_data // 8)]
    raw_bits = bytes_to_bits(data, n_data)

    if config.bch_enabled:
        chunk_data = DATA_LEN
        chunk_total = DATA_LEN + 8
        n_chunks = min((n_data + chunk_data - 1) // chunk_data, avail // chunk_total)
        if n_chunks == 0:
            raise ValueError("Not enough capacity for BCH encoding")
        parts = []
        for i in range(n_chunks):
            start = i * chunk_data
            end = min(start + chunk_data, n_data)
            chunk = np.zeros(chunk_data, dtype=np.int8)
            chunk[:end - start] = raw_bits[start:end]
            parts.append(bch_encode(chunk))
        payload = np.concatenate(parts)
    else:
        max_payload = min(n_data, avail)
        payload = raw_bits[:max_payload]

    if config.sync_enabled:
        payload = build_payload(sync, payload)

    return payload


def _extract_payload(all_bits: np.ndarray, config: WatermarkConfig) -> tuple:
    sync = generate_sync_pattern(config.sync_seed)
    if config.sync_enabled:
        offset, corr = correlate_sync(all_bits, sync)
        if offset >= 0 and corr >= 0.5:
            payload_bits = all_bits[offset + len(sync):]
        else:
            payload_bits = all_bits
    else:
        payload_bits = all_bits
        corr = 0.0

    if config.bch_enabled:
        chunk_size = DATA_LEN + 8
        n = len(payload_bits) // chunk_size
        if n > 0:
            parts = []
            for i in range(n):
                chunk = payload_bits[i * chunk_size:(i + 1) * chunk_size]
                if len(chunk) == chunk_size:
                    parts.append(bch_decode(chunk))
            payload_bits = np.concatenate(parts) if parts else payload_bits

    payload_bits = payload_bits[:64]
    return bits_to_bytes(payload_bits), corr


def embed_watermark(carrier: Image.Image, watermark_data: bytes, config: WatermarkConfig = None) -> tuple:
    if config is None:
        config = WatermarkConfig()

    divisor = 8 * (2 ** config.level)
    new_w = (carrier.size[0] // divisor) * divisor
    new_h = (carrier.size[1] // divisor) * divisor
    if new_w < divisor or new_h < divisor:
        raise ValueError(f"Image too small: minimum {divisor}x{divisor} pixels for level={config.level}")

    carrier = carrier.resize((new_w, new_h), Image.LANCZOS)
    carrier_rgb = carrier.convert('RGB')
    r, g, b = carrier_rgb.split()
    r_arr, g_arr, b_arr = [np.array(x, dtype=np.float64) for x in (r, g, b)]

    y = r_arr * 0.299 + g_arr * 0.587 + b_arr * 0.114
    original_y = y.copy()
    full = get_full_coeffs(y, config.level)
    ll_full = full[0].copy()

    blocks, ll_shape = dct_blockwise(full[0])
    n_avail = blocks.shape[0]
    payload = _calc_payload(watermark_data, config, n_avail)

    modified = embed_bits_in_blocks(blocks, payload, config.delta, len(payload))
    ll_rebuilt = idct_blockwise(modified, ll_shape)

    y_watermarked = reconstruct_from_ll(ll_rebuilt, full, config.level)
    y_watermarked = np.clip(y_watermarked, 0, 255).astype(np.uint8)

    dy = y_watermarked.astype(np.float64) - original_y.astype(np.float64)
    ro = np.clip(r_arr + dy, 0, 255).astype(np.uint8)
    go = np.clip(g_arr + dy, 0, 255).astype(np.uint8)
    bo = np.clip(b_arr + dy, 0, 255).astype(np.uint8)

    result = Image.fromarray(np.stack([ro, go, bo], axis=2), 'RGB')
    p = round(psnr(np.array(carrier_rgb), np.array(result)), 2)
    s = round(ssim(np.array(r, dtype=np.float64), ro.astype(np.float64)), 4)

    return result, {'psnr': p, 'ssim': s, 'bits_embedded': len(payload)}


def extract_watermark(stego: Image.Image, config: WatermarkConfig = None) -> tuple:
    if config is None:
        config = WatermarkConfig()

    divisor = 8 * (2 ** config.level)
    new_w = (stego.size[0] // divisor) * divisor
    new_h = (stego.size[1] // divisor) * divisor
    stego = stego.resize((new_w, new_h), Image.LANCZOS).convert('RGB')
    r, g, b = stego.split()
    y = np.array(r, dtype=np.float64) * 0.299 + np.array(g, dtype=np.float64) * 0.587 + np.array(b, dtype=np.float64) * 0.114

    full = get_full_coeffs(y, config.level)
    blocks, _ = dct_blockwise(full[0])
    n_bits = min(blocks.shape[0], 256)
    all_bits = extract_bits_from_blocks(blocks, config.delta, n_bits)

    raw, corr = _extract_payload(all_bits, config)
    return raw, {'sync_corr': round(float(corr), 4)}
