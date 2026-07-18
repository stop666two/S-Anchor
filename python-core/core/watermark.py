import numpy as np
from PIL import Image

from .config import WatermarkConfig
from .dwt import get_full_coeffs, reconstruct_from_ll
from .dct import dct_blockwise, idct_blockwise
from .svd_qim import embed_bits_in_blocks, extract_bits_from_blocks
from .sync_pattern import generate_sync_pattern, correlate_sync
from .bch_codec import encode as bch_encode, decode as bch_decode, bytes_to_bits, bits_to_bytes, DATA_LEN, CODE_LEN
from .metrics import psnr, ssim

SYNC_LEN = 64


def _make_payload(data: bytes, config: WatermarkConfig, n_blocks: int):
    sync = generate_sync_pattern(config.sync_seed)
    n_sync = SYNC_LEN if config.sync_enabled else 0
    n_data = len(data)
    avail_data_bits = (n_blocks - n_sync)
    if avail_data_bits < 8:
        raise ValueError('Image too small: need at least %d blocks for sync' % (n_sync + 8))

    if config.bch_enabled:
        n_bch = max(1, avail_data_bits // CODE_LEN)
        used = n_bch * CODE_LEN
        data_bits_needed = n_bch * DATA_LEN
        data_bits = bytes_to_bits(data, min(n_data * 8, data_bits_needed))
        if len(data_bits) < data_bits_needed:
            data_bits = np.pad(data_bits, (0, data_bits_needed - len(data_bits)), 'constant')
        chunks = []
        for i in range(n_bch):
            chunk = data_bits[i * DATA_LEN:(i + 1) * DATA_LEN]
            chunks.append(bch_encode(chunk))
        payload = np.concatenate(chunks)
    else:
        used = min(avail_data_bits, n_data * 8)
        used = min(used, 256)
        payload = bytes_to_bits(data, used)

    if config.sync_enabled:
        payload = np.concatenate([sync, payload])

    if len(payload) > n_blocks:
        payload = payload[:n_blocks]
    elif len(payload) < n_blocks:
        payload = np.pad(payload, (0, n_blocks - len(payload)), 'constant')

    return payload, used + n_sync


def _read_payload(all_bits: np.ndarray, config: WatermarkConfig):
    sync = generate_sync_pattern(config.sync_seed)
    if config.sync_enabled:
        offset, corr = correlate_sync(all_bits, sync)
        found = corr >= 0.5 and offset >= 0
        if found:
            payload = all_bits[offset + SYNC_LEN:]
        else:
            payload = all_bits
    else:
        payload = all_bits
        corr = 0.0
        found = True

    if config.bch_enabled:
        n_chunks = len(payload) // CODE_LEN
        if n_chunks > 0:
            parts = []
            for i in range(n_chunks):
                chunk = payload[i * CODE_LEN:(i + 1) * CODE_LEN]
                if len(chunk) == CODE_LEN:
                    dec = bch_decode(chunk)
                    parts.append(dec)
            payload = np.concatenate(parts) if parts else payload

    max_bytes = min(len(payload) // 8, 64)
    payload = payload[:max_bytes * 8]
    return bits_to_bytes(payload), corr, found


def _auto_level(img_w: int, img_h: int, config: WatermarkConfig) -> int:
    needed = 64 + 64  # sync + reasonable data
    if config.bch_enabled:
        needed = ((needed + 6) // 7) * 15 + 64
    for level in range(config.level, 0, -1):
        d = 8 * (2 ** level)
        w = (img_w // d) * d
        h = (img_h // d) * d
        if w < d or h < d:
            continue
        blocks = (w // (8 << level)) * (h // (8 << level))
        if blocks >= needed:
            return level
    return 1


def embed_watermark(carrier: Image.Image, watermark_data: bytes, config: WatermarkConfig = None) -> tuple:
    if config is None:
        config = WatermarkConfig()
    level = _auto_level(carrier.size[0], carrier.size[1], config)
    config = WatermarkConfig(**{**config.__dict__, 'level': level})

    divisor = 8 * (1 << level)
    w, h = carrier.size
    carrier = carrier.resize(((w // divisor) * divisor, (h // divisor) * divisor), Image.LANCZOS)
    carrier_rgb = carrier.convert('RGB')
    r, g, b = carrier_rgb.split()
    ra, ga, ba = [np.array(x, np.float64) for x in (r, g, b)]
    y = ra * 0.299 + ga * 0.587 + ba * 0.114
    orig_y = y.copy()
    coeffs = get_full_coeffs(y, level)
    blocks, shp = dct_blockwise(coeffs[0])

    payload, n_used = _make_payload(watermark_data, config, blocks.shape[0])
    modified = embed_bits_in_blocks(blocks, payload, config.delta, 0)
    ll2 = idct_blockwise(modified, shp)
    y2 = reconstruct_from_ll(ll2, coeffs, level)
    y2 = np.clip(y2, 0, 255).astype(np.uint8)

    dy = y2.astype(np.float64) - orig_y.astype(np.float64)
    ro = np.clip(ra + dy, 0, 255).astype(np.uint8)
    go = np.clip(ga + dy, 0, 255).astype(np.uint8)
    bo = np.clip(ba + dy, 0, 255).astype(np.uint8)
    result = Image.fromarray(np.stack([ro, go, bo], axis=2), 'RGB')

    p = round(psnr(np.array(carrier_rgb), np.array(result)), 2)
    ym = ro.astype(np.float64) * 0.299 + go.astype(np.float64) * 0.587 + bo.astype(np.float64) * 0.114
    s = round(ssim(y.astype(np.float64), ym), 4)
    return result, {'psnr': p, 'ssim': s, 'bits_embedded': n_used, 'level_used': level}


def extract_watermark(stego: Image.Image, config: WatermarkConfig = None) -> tuple:
    if config is None:
        config = WatermarkConfig()
    level = _auto_level(stego.size[0], stego.size[1], config)
    config = WatermarkConfig(**{**config.__dict__, 'level': level})

    divisor = 8 * (1 << level)
    w, h = stego.size
    stego = stego.resize(((w // divisor) * divisor, (h // divisor) * divisor), Image.LANCZOS).convert('RGB')
    r, g, b = stego.split()
    y = np.array(r, np.float64) * 0.299 + np.array(g, np.float64) * 0.587 + np.array(b, np.float64) * 0.114

    coeffs = get_full_coeffs(y, level)
    blocks, _ = dct_blockwise(coeffs[0])
    all_bits = extract_bits_from_blocks(blocks, config.delta, blocks.shape[0])

    raw, corr, found = _read_payload(all_bits, config)
    return raw, {'sync_corr': round(float(corr), 4), 'sync_found': found}
