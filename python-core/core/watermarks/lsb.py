import struct
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
        max_bits = h * w * 3
        # Prepend 2-byte length header
        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        if len(bits) > max_bits:
            raise ValueError(f'LSB payload too large: {len(bits)} bits, max {max_bits}')
        flat = arr.reshape(-1)
        flat[:len(bits)] = (flat[:len(bits)] & 0xFE) | bits
        result = Image.fromarray(arr, 'RGB')
        return result, {'bits_embedded': len(bits), 'capacity': max_bits}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'))
        flat = arr.reshape(-1)
        # Read 16-bit length header (first 16 LSBs)
        header_bits = flat[:16] & 1
        data_len = struct.unpack('>H', np.packbits(header_bits.astype(np.uint8)).tobytes())[0]
        if data_len < 1 or data_len > 65535:
            return b'', {'bits_extracted': 0}
        n_bits = 16 + data_len * 8
        if n_bits > len(flat):
            return b'', {'bits_extracted': 0}
        bits = flat[16:n_bits] & 1
        payload = np.packbits(bits.astype(np.uint8)).tobytes()
        return payload, {'bits_extracted': len(bits)}


register(LsbWatermark())
