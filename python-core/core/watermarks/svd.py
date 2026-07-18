import struct
import numpy as np
from PIL import Image
from numpy.typing import NDArray

from . import BaseWatermark, register


class SvdWatermark(BaseWatermark):
    type_id = 'svd'
    name = 'SVD Singular Value'

    def embed_order(self) -> int:
        return 25

    def extract_order(self) -> int:
        return 45

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        rgb = np.array(carrier.convert('RGB'), dtype=np.float64)
        # Use G channel (shared with DFT's old channel)
        arr = rgb[:,:,1].copy()
        strength = params.get('strength', 25.0)
        block_size = 8

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        h, w = arr.shape
        h_blocks = h // block_size
        w_blocks = w // block_size
        n_blocks = h_blocks * w_blocks

        if len(bits) > n_blocks:
            raise ValueError(f'SVD payload too large: {len(bits)} bits, {n_blocks} blocks')

        modified = arr.copy()
        bi = 0
        for by in range(h_blocks):
            for bx in range(w_blocks):
                if bi >= len(bits):
                    break
                y1, y2 = by * block_size, (by + 1) * block_size
                x1, x2 = bx * block_size, (bx + 1) * block_size
                block = arr[y1:y2, x1:x2]
                u, s, vt = np.linalg.svd(block, full_matrices=False)
                q = int(round(s[0] / strength))
                q = (int(q / 2) * 2) | int(bits[bi])
                s[0] = max(1.0, float(q * strength))
                modified[y1:y2, x1:x2] = (u * s) @ vt
                bi += 1

        rgb[:,:,1] = np.clip(modified, 0, 255)
        return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), {'bits_embedded': len(bits)}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'), dtype=np.float64)[:,:,1]
        strength = params.get('strength', 25.0)
        block_size = 8
        h, w = arr.shape
        h_blocks = h // block_size
        w_blocks = w // block_size

        bits = []
        for by in range(h_blocks):
            for bx in range(w_blocks):
                y1, y2 = by * block_size, (by + 1) * block_size
                x1, x2 = bx * block_size, (bx + 1) * block_size
                block = arr[y1:y2, x1:x2]
                _, s, _ = np.linalg.svd(block, full_matrices=False)
                q = int(round(s[0] / strength))
                bits.append(q % 2)

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


register(SvdWatermark())
