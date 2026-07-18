import struct
import numpy as np
from PIL import Image
from numpy.typing import NDArray

from . import BaseWatermark, register


class SpreadWatermark(BaseWatermark):
    type_id = 'spread'
    name = 'Spread Spectrum'

    def embed_order(self) -> int:
        return 30

    def extract_order(self) -> int:
        return 40

    def _pn_seq(self, seed: int, length: int) -> NDArray:
        rng = np.random.default_rng(seed)
        return rng.choice([-1, 1], size=length)

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        arr = np.array(carrier.convert('RGB'), dtype=np.float64)[:,:,2]
        strength = params.get('strength', 6.0)
        seed = params.get('seed', 42)
        h, w = arr.shape
        total_pixels = h * w

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        bits_per_pixel = max(1, params.get('spread_factor', 64))
        needed_pixels = len(bits) * bits_per_pixel
        if needed_pixels > total_pixels:
            raise ValueError(f'Spread payload too large: {needed_pixels} pixels needed, max {total_pixels}')

        modified = arr.copy().reshape(-1)
        for i in range(len(bits)):
            start = i * bits_per_pixel
            end = min(start + bits_per_pixel, total_pixels)
            seg_len = end - start
            pn = self._pn_seq(seed + i, seg_len)
            bit_val = 1 if bits[i] == 1 else -1
            modified[start:end] += pn * strength * bit_val

        result = np.clip(modified, 0, 255).reshape(h, w).astype(np.uint8)
        result_rgb = np.array(carrier.convert('RGB'), dtype=np.float64); result_rgb[:,:,2] = result; return Image.fromarray(np.clip(result_rgb,0,255).astype(np.uint8),'RGB'), {
            'bits_embedded': len(bits),
            'spread_factor': bits_per_pixel,
        }

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'), dtype=np.float64)[:,:,2]
        h, w = arr.shape
        seed = params.get('seed', 42)
        bits_per_pixel = params.get('spread_factor', 64)
        flat = arr.reshape(-1)
        total_pixels = len(flat)

        # Read 16-bit length: need 16 * bits_per_pixel pixels
        header_pixels = 16 * bits_per_pixel
        if header_pixels > total_pixels:
            return b'', {'bits_extracted': 0}

        header_bits = np.zeros(16, dtype=np.uint8)
        for i in range(16):
            start = i * bits_per_pixel
            end = min(start + bits_per_pixel, total_pixels)
            seg = flat[start:end]
            pn = self._pn_seq(seed + i, end - start)
            corr = np.dot(seg - np.mean(seg), pn)
            header_bits[i] = 1 if corr > 0 else 0

        data_len = struct.unpack('>H', np.packbits(header_bits).tobytes())[0]
        if data_len < 1 or data_len > 4096:
            return b'', {'bits_extracted': 0}

        n_bits = 16 + data_len * 8
        bits = np.zeros(n_bits - 16, dtype=np.uint8)
        for i in range(16, n_bits):
            start = i * bits_per_pixel
            end = min(start + bits_per_pixel, total_pixels)
            if end - start < 1:
                break
            seg = flat[start:end]
            pn = self._pn_seq(seed + i, end - start)
            corr = np.dot(seg - np.mean(seg), pn)
            bits[i - 16] = 1 if corr > 0 else 0

        payload = np.packbits(bits).tobytes()
        return payload, {'bits_extracted': len(bits)}


register(SpreadWatermark())
