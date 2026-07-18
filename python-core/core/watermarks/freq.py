import numpy as np
from PIL import Image
from numpy.typing import NDArray

from ..config import WatermarkConfig
from ..dwt import get_full_coeffs, reconstruct_from_ll
from ..dct import dct_blockwise, idct_blockwise
from ..svd_qim import embed_bits_in_blocks, extract_bits_from_blocks
from ..sync_pattern import generate_sync_pattern, correlate_sync
from ..bch_codec import encode as bch_encode, decode as bch_decode, bytes_to_bits, bits_to_bytes, DATA_LEN, CODE_LEN
from ..metrics import psnr, ssim
from . import BaseWatermark, register

SYNC_LEN = 64


class FreqWatermark(BaseWatermark):
    type_id = 'freq'
    name = 'Frequency Domain (DWT-DCT-SVD)'

    def embed_order(self) -> int:
        return 10

    def extract_order(self) -> int:
        return 60

    def _make_config(self, params: dict) -> WatermarkConfig:
        return WatermarkConfig(
            alpha=params.get('alpha', 0.15),
            delta=params.get('delta', 36.0),
            level=params.get('level', 2),
            sync_enabled=params.get('sync', True),
            bch_enabled=params.get('bch', True),
        )

    def _auto_level(self, img_w: int, img_h: int, config: WatermarkConfig) -> int:
        needed = 64 + 64
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

    def _make_payload(self, data: bytes, config: WatermarkConfig, n_blocks: int) -> tuple[NDArray, int]:
        sync = generate_sync_pattern(config.sync_seed)
        n_sync = SYNC_LEN if config.sync_enabled else 0
        n_data = len(data)
        avail_data_bits = n_blocks - n_sync
        if avail_data_bits < 8:
            raise ValueError('Image too small for freq watermark')

        if config.bch_enabled:
            n_bch = max(1, avail_data_bits // CODE_LEN)
            used = n_bch * CODE_LEN
            data_bits_needed = n_bch * DATA_LEN
            n_data_bits = n_data * 8
            if n_data_bits > data_bits_needed:
                raise ValueError(
                f'Freq watermark too long: {n_data} bytes exceeds capacity '
                f'{data_bits_needed//8} bytes. Password adds ~22 bytes overhead. '
                f'Try: larger image (512x512), turn off SYNC/BCH, or use LSB type.'
            )
            data_bits = bytes_to_bits(data, n_data_bits)
            if len(data_bits) < data_bits_needed:
                data_bits = np.pad(data_bits, (0, data_bits_needed - len(data_bits)), 'constant')
            chunks = [bch_encode(data_bits[i * DATA_LEN:(i + 1) * DATA_LEN]) for i in range(n_bch)]
            payload = np.concatenate(chunks)
        else:
            capacity = min(avail_data_bits, 512)
            n_data_bits = n_data * 8
            if n_data_bits > capacity:
                raise ValueError(
                    f'Freq watermark too long: need {n_data_bits} bits, capacity {capacity} bits'
                )
            used = n_data_bits
            payload = bytes_to_bits(data, used)

        if config.sync_enabled:
            payload = np.concatenate([sync, payload])
        if len(payload) > n_blocks:
            payload = payload[:n_blocks]
        elif len(payload) < n_blocks:
            payload = np.pad(payload, (0, n_blocks - len(payload)), 'constant')
        return payload, used + n_sync

    def _read_payload(self, all_bits: NDArray, config: WatermarkConfig) -> tuple[bytes, float, bool]:
        sync = generate_sync_pattern(config.sync_seed)
        if config.sync_enabled:
            offset, corr = correlate_sync(all_bits, sync)
            found = corr >= 0.5 and offset >= 0
            payload = all_bits[offset + SYNC_LEN:] if found else all_bits
        else:
            payload = all_bits
            corr = 0.0
            found = True

        if config.bch_enabled:
            n_chunks = len(payload) // CODE_LEN
            if n_chunks > 0:
                parts = [bch_decode(payload[i * CODE_LEN:(i + 1) * CODE_LEN]) for i in range(n_chunks)
                         if len(payload[i * CODE_LEN:(i + 1) * CODE_LEN]) == CODE_LEN]
                payload = np.concatenate(parts) if parts else payload

        max_bytes = min(len(payload) // 8, 64)
        raw = bits_to_bytes(payload[:max_bytes * 8])
        # Strip null bytes and BCH padding artifacts
        null_pos = raw.find(b'\x00')
        if null_pos >= 0:
            raw = raw[:null_pos]
        while raw and raw[-1] < 32 and raw[-1] not in (9, 10, 13):
            raw = raw[:-1]
        return raw, corr, found

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        config = self._make_config(params)
        level = self._auto_level(carrier.size[0], carrier.size[1], config)
        config.level = level

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
        payload_bits, n_used = self._make_payload(payload, config, blocks.shape[0])
        modified = embed_bits_in_blocks(blocks, payload_bits, config.delta, 0)

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

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        config = self._make_config(params)
        level = self._auto_level(stego.size[0], stego.size[1], config)
        config.level = level

        divisor = 8 * (1 << level)
        w, h = stego.size
        stego = stego.resize(((w // divisor) * divisor, (h // divisor) * divisor), Image.LANCZOS).convert('RGB')
        r, g, b = stego.split()
        y = np.array(r, np.float64) * 0.299 + np.array(g, np.float64) * 0.587 + np.array(b, np.float64) * 0.114

        coeffs = get_full_coeffs(y, level)
        blocks, _ = dct_blockwise(coeffs[0])
        all_bits = extract_bits_from_blocks(blocks, config.delta, blocks.shape[0])

        raw, corr, found = self._read_payload(all_bits, config)
        return raw, {'sync_corr': round(float(corr), 4), 'sync_found': found}


register(FreqWatermark())
