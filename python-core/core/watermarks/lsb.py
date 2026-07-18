import numpy as np
from PIL import Image
from numpy.typing import NDArray

from . import BaseWatermark, register


class LsbWatermark(BaseWatermark):
    type_id = 'lsb'
    name = 'LSB Steganography'

    def embed_order(self) -> int:
        return 50

    def extract_order(self) -> int:
        return 20

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        arr = np.array(carrier.convert('RGB'))
        h, w, _ = arr.shape
        bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
        max_bits = h * w * 3
        if len(bits) > max_bits:
            raise ValueError(f'LSB payload too large: {len(bits)} bits, max {max_bits}')
        flat = arr.reshape(-1)
        flat[:len(bits)] = (flat[:len(bits)] & 0xFE) | bits
        result = Image.fromarray(arr, 'RGB')
        return result, {'bits_embedded': len(bits), 'capacity': max_bits}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        n_bits = params.get('n_bits', 0)
        arr = np.array(stego.convert('RGB'))
        flat = arr.reshape(-1)
        if n_bits > 0:
            bits = flat[:n_bits] & 1
        else:
            bits = flat & 1
        payload = np.packbits(bits.astype(np.uint8)).tobytes().rstrip(b'\x00')
        return payload, {'bits_extracted': len(bits)}


register(LsbWatermark())
