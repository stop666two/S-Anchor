import numpy as np
from PIL import Image

from .config import WatermarkConfig
from .dwt import decompose_y_channel, get_full_coeffs, reconstruct_from_ll
from .dct import dct_blockwise, idct_blockwise
from .svd_qim import embed_bits_in_blocks, extract_bits_from_blocks
from .sync_pattern import generate_sync_pattern, correlate_sync, build_payload, SYNC_LEN
from .bch_codec import encode as bch_encode, decode as bch_decode, bytes_to_bits, bits_to_bytes, DATA_LEN
from .metrics import psnr, ssim

DATA_BITS = 64


def _prepare_payload(watermark_data: bytes, config: WatermarkConfig) -> np.ndarray:
    if config.bch_enabled:
        n_chunks = (len(watermark_data) * 8 + DATA_LEN - 1) // DATA_LEN
        all_data_bits = bytes_to_bits(watermark_data, n_chunks * DATA_LEN)
        payload_parts = []
        for i in range(n_chunks):
            chunk = all_data_bits[i * DATA_LEN:(i + 1) * DATA_LEN]
            payload_parts.append(bch_encode(chunk))
        payload = np.concatenate(payload_parts)
    else:
        payload = bytes_to_bits(watermark_data, DATA_BITS)

    if config.sync_enabled:
        sync = generate_sync_pattern(config.sync_seed)
        payload = build_payload(sync, payload)

    return payload


def _extract_payload(all_bits: np.ndarray, config: WatermarkConfig) -> tuple:
    if config.sync_enabled:
        sync = generate_sync_pattern(config.sync_seed)
        offset, corr = correlate_sync(all_bits, sync)
        if offset >= 0 and corr >= 0.5:
            payload_start = offset + len(sync)
            payload_bits = all_bits[payload_start:]
        else:
            payload_bits = all_bits
    else:
        payload_bits = all_bits
        corr = 0.0

    if config.bch_enabled:
        n_bch_chunks = len(payload_bits) // (DATA_LEN + 8)
        if n_bch_chunks == 0:
            n_bch_chunks = 1
        chunk_size = DATA_LEN + 8
        decoded_parts = []
        for i in range(n_bch_chunks):
            chunk = payload_bits[i * chunk_size:(i + 1) * chunk_size]
            if len(chunk) == chunk_size:
                decoded_parts.append(bch_decode(chunk))
        if decoded_parts:
            payload_bits = np.concatenate(decoded_parts)

    payload_bits = payload_bits[:DATA_BITS]
    raw = bits_to_bytes(payload_bits)
    return raw, corr


def embed_watermark(
    carrier: Image.Image,
    watermark_data: bytes,
    config: WatermarkConfig = None
) -> tuple:
    if config is None:
        config = WatermarkConfig()

    divisor = 8 * (2 ** config.level)
    w, h = carrier.size
    new_w = (w // divisor) * divisor
    new_h = (h // divisor) * divisor
    if new_w < divisor or new_h < divisor:
        raise ValueError(f"Image too small: need at least {divisor}x{divisor}")
    carrier_resized = carrier.resize((new_w, new_h), Image.LANCZOS)

    carrier_rgb = carrier_resized.convert('RGB')
    r, g, b = carrier_rgb.split()
    r_arr = np.array(r, dtype=np.float64)
    g_arr = np.array(g, dtype=np.float64)
    b_arr = np.array(b, dtype=np.float64)
    y_channel = r_arr * 0.299 + g_arr * 0.587 + b_arr * 0.114

    original_y = y_channel.copy()
    full_coeffs = get_full_coeffs(y_channel, config.level)
    ll = full_coeffs[0]

    dct_blocks, ll_shape = dct_blockwise(ll)
    n_available = dct_blocks.shape[0]

    payload = _prepare_payload(watermark_data, config)
    n_bits = len(payload)
    assert n_bits <= n_available, f"Need {n_bits} blocks, have {n_available}"

    modified_dct = embed_bits_in_blocks(dct_blocks, payload, config.delta, len(payload))
    modified_ll = idct_blockwise(modified_dct, ll_shape)

    watermarked_y = reconstruct_from_ll(modified_ll, full_coeffs, config.level)
    watermarked_y = np.clip(watermarked_y, 0, 255).astype(np.uint8)

    diff = watermarked_y.astype(np.float64) - original_y.astype(np.float64)
    r_out = np.clip(r_arr + diff, 0, 255).astype(np.uint8)
    g_out = np.clip(g_arr + diff, 0, 255).astype(np.uint8)
    b_out = np.clip(b_arr + diff, 0, 255).astype(np.uint8)

    result = Image.fromarray(np.stack([r_out, g_out, b_out], axis=2), 'RGB')
    psnr_val = round(psnr(np.array(carrier_rgb), np.array(result)), 2)
    ssim_val = round(ssim(np.array(r, dtype=np.float64), r_out.astype(np.float64)), 4)

    if carrier.size != (new_w, new_h):
        result = result.resize(carrier.size, Image.LANCZOS)

    return result, {
        'psnr': psnr_val,
        'ssim': ssim_val,
        'bits_embedded': n_bits,
        'blocks_used': n_bits,
    }


def extract_watermark(
    stego: Image.Image,
    config: WatermarkConfig = None
) -> tuple:
    if config is None:
        config = WatermarkConfig()

    divisor = 8 * (2 ** config.level)
    w, h = stego.size
    new_w = (w // divisor) * divisor
    new_h = (h // divisor) * divisor
    stego = stego.resize((new_w, new_h), Image.LANCZOS)

    stego_rgb = stego.convert('RGB')
    r, g, b = stego_rgb.split()
    y_channel = np.array(r, dtype=np.float64) * 0.299 + np.array(g, dtype=np.float64) * 0.587 + np.array(b, dtype=np.float64) * 0.114

    full_coeffs = get_full_coeffs(y_channel, config.level)
    ll = full_coeffs[0]
    dct_blocks, _ = dct_blockwise(ll)
    n_available = dct_blocks.shape[0]

    max_bits = min(n_available, DATA_BITS + 128)
    all_bits = extract_bits_from_blocks(dct_blocks, config.delta, max_bits)

    raw, corr = _extract_payload(all_bits, config)
    return raw, {'sync_corr': round(float(corr), 4)}
