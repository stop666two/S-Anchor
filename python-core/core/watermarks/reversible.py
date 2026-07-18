import struct

import numpy as np
from PIL import Image

from . import BaseWatermark, register

MAGIC = 0x5A  # verification byte


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

        # Format: magic(1) + length(2) + payload
        magic_byte = bytes([MAGIC])
        data = magic_byte + struct.pack('>H', len(payload)) + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        max_bits = h * w - 8  # leave margin
        if len(bits) > max_bits:
            raise ValueError('Reversible payload too large')

        modified = arr.copy()
        for i in range(len(bits)):
            y, x = divmod(i, w)
            orig_bit1 = (int(modified[y, x, 0]) >> 1) & 1
            modified[y, x, 0] = (modified[y, x, 0] & 0xFD) | (bits[i] << 1)
            modified[y, x, 1] = (modified[y, x, 1] & 0xFD) | (orig_bit1 << 1)

        return Image.fromarray(modified, 'RGB'), {'bits_embedded': len(bits)}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'), dtype=np.uint8)
        h, w, _ = arr.shape

        bits = []
        for i in range(min(h * w, 2048)):  # limit scan
            y, x = divmod(i, w)
            bits.append((arr[y, x, 0] >> 1) & 1)

            if len(bits) == 8:
                magic = np.packbits(np.array(bits[:8], dtype=np.uint8)).tobytes()[0]
                if magic != MAGIC:
                    return b'', {'bits_extracted': 0}

            if len(bits) >= 24:  # 8 magic + 16 length
                len_bits = np.array(bits[8:24], dtype=np.uint8)
                data_len = struct.unpack('>H', np.packbits(len_bits).tobytes())[0]
                if data_len < 1 or data_len > 1024:
                    return b'', {'bits_extracted': 0}
                n_needed = 24 + data_len * 8
                if len(bits) >= n_needed:
                    payload_bits = np.array(bits[24:n_needed], dtype=np.uint8)
                    payload = np.packbits(payload_bits).tobytes()
                    return payload, {'bits_extracted': len(payload_bits)}

        return b'', {'bits_extracted': 0}


register(ReversibleWatermark())
