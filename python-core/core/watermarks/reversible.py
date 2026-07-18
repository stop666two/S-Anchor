import struct
import numpy as np
from PIL import Image
from numpy.typing import NDArray

from . import BaseWatermark, register


class ReversibleWatermark(BaseWatermark):
    type_id = 'reversible'
    name = 'Reversible (Lossless)'

    def embed_order(self) -> int:
        return 45

    def extract_order(self) -> int:
        return 25

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        arr = np.array(carrier.convert('RGB'), dtype=np.int16)
        h, w, _ = arr.shape

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        # Use pixel pairs (R,G), (B,R), (G,B) etc.
        pairs = h * w
        if len(bits) > pairs:
            raise ValueError(f'Reversible payload too large: {len(bits)} bits, max {pairs}')

        modified = arr.copy()
        bi = 0
        loc_map = []
        for y in range(h):
            for x in range(w):
                if bi >= len(bits):
                    break
                a, b = int(modified[y, x, 0]), int(modified[y, x, 1])
                diff = b - a
                if diff < -128 or diff > 127:
                    continue
                a_new = a - (diff + 1) // 2
                b_new = b + diff // 2
                if a_new < 0 or a_new > 255 or b_new < 0 or b_new > 255:
                    loc_map.append((y, x, 0))
                    continue
                bit = bits[bi]
                if bit == 1:
                    modified[y, x, 0] = a_new
                    modified[y, x, 1] = b_new
                    loc_map.append((y, x, 1))
                else:
                    modified[y, x, 0] = a_new
                    modified[y, x, 1] = b_new
                    loc_map.append((y, x, 0))
                bi += 1

        result = np.clip(modified, 0, 255).astype(np.uint8)
        return Image.fromarray(result, 'RGB'), {
            'bits_embedded': bi,
            'loc_map_size': len(loc_map),
        }

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'), dtype=np.int16)
        h, w, _ = arr.shape

        bits = []
        for y in range(h):
            for x in range(w):
                a, b = int(arr[y, x, 0]), int(arr[y, x, 1])
                diff = b - a
                a_orig = a + (diff + 1) // 2
                b_orig = b - diff // 2
                if a_orig < 0 or a_orig > 255 or b_orig < 0 or b_orig > 255:
                    continue
                diff_orig = b_orig - a_orig
                if abs(diff_orig) > 255:
                    continue
                bits.append(diff_orig % 2)

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
