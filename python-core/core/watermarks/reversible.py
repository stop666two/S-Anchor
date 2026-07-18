import struct
import numpy as np
from PIL import Image

from . import BaseWatermark, register


class ReversibleWatermark(BaseWatermark):
    type_id = 'reversible'
    name = 'Reversible (Lossless)'

    def embed_order(self) -> int:
        return 45

    def extract_order(self) -> int:
        return 25

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        arr = np.array(carrier.convert('RGB'), dtype=np.uint8)
        h, w, _ = arr.shape

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        max_bits = h * w
        if len(bits) > max_bits:
            raise ValueError(f'Reversible payload too large: {len(bits)} bits, max {max_bits}')

        modified = arr.copy()
        # For each pixel: embed bit in R's LSB, save original R's LSB in G's LSB
        for i in range(len(bits)):
            y, x = divmod(i, w)
            orig_lsb = int(modified[y, x, 0]) & 1
            modified[y, x, 0] = (modified[y, x, 0] & 0xFE) | bits[i]
            modified[y, x, 1] = (modified[y, x, 1] & 0xFE) | orig_lsb

        return Image.fromarray(modified, 'RGB'), {'bits_embedded': len(bits)}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'), dtype=np.uint8)
        h, w, _ = arr.shape

        bits = []
        for i in range(h * w):
            y, x = divmod(i, w)
            bits.append(arr[y, x, 0] & 1)
            if len(bits) >= 16:
                header_bits = np.array(bits[:16], dtype=np.uint8)
                data_len = struct.unpack('>H', np.packbits(header_bits).tobytes())[0]
                if data_len < 1 or data_len > 4096:
                    return b'', {'bits_extracted': 0}
                n_needed = 16 + data_len * 8
                if len(bits) >= n_needed:
                    payload_bits = np.array(bits[16:n_needed], dtype=np.uint8)
                    payload = np.packbits(payload_bits).tobytes()
                    return payload, {'bits_extracted': len(payload_bits)}

        return b'', {'bits_extracted': 0}


register(ReversibleWatermark())
