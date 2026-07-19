import struct

import numpy as np
from numpy.fft import fft2, ifft2
from PIL import Image

from ..bch_codec import CODE_LEN, DATA_LEN
from ..bch_codec import decode as bch_decode
from ..bch_codec import encode as bch_encode
from . import BaseWatermark, register


class DftWatermark(BaseWatermark):
    type_id = 'dft'
    name = 'DFT Phase Modulation'

    def embed_order(self) -> int:
        return 20

    def extract_order(self) -> int:
        return 50

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        arr = np.array(carrier.convert('RGB'), dtype=np.float64)
        lum = 0.299 * arr[:,:,0] + 0.587 * arr[:,:,1] + 0.114 * arr[:,:,2]
        strength = params.get('strength', 15.0)
        block_size = 8

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        raw_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        n_bch = max(1, (len(raw_bits) + DATA_LEN - 1) // DATA_LEN)
        raw_bits = np.pad(raw_bits, (0, n_bch * DATA_LEN - len(raw_bits)), 'constant')
        chunks = [bch_encode(raw_bits[i * DATA_LEN:(i + 1) * DATA_LEN]) for i in range(n_bch)]
        bits = np.concatenate(chunks)

        h, w = lum.shape
        h_blocks, w_blocks = h // block_size, w // block_size
        n_blocks = h_blocks * w_blocks

        if len(bits) > n_blocks:
            raise ValueError(f'DFT payload too large: need {len(bits)} blocks, only {n_blocks} available')

        modified = lum.copy()
        bi = 0
        for by in range(h_blocks):
            for bx in range(w_blocks):
                if bi >= len(bits):
                    break
                y1, y2 = by * block_size, (by + 1) * block_size
                x1, x2 = bx * block_size, (bx + 1) * block_size
                block = lum[y1:y2, x1:x2]
                fft_c = fft2(block)
                mid = np.abs(fft_c[1, 2])
                q = int(round(mid / strength))
                if bits[bi]:
                    q = (int(q / 2) * 2) | 1
                else:
                    q = (int(q / 2) * 2)
                ratio = max(0.5, q * strength) / max(0.5, mid)
                fft_c[1, 2] *= ratio
                ci2, cj2 = (block_size - 1) % block_size, (block_size - 2) % block_size
                if ci2 != 1 or cj2 != 2:
                    fft_c[ci2, cj2] = np.conj(fft_c[1, 2])
                modified[y1:y2, x1:x2] = np.real(ifft2(fft_c))
                bi += 1

        modified = np.clip(modified, 0, 255)
        lum_diff = modified - lum
        for c in range(3):
            arr[:,:,c] += lum_diff
        return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB'), {
            'bits_embedded': len(bits),
        }

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'), dtype=np.float64)
        lum = 0.299 * arr[:,:,0] + 0.587 * arr[:,:,1] + 0.114 * arr[:,:,2]
        strength = params.get('strength', 15.0)
        block_size = 8
        h, w = lum.shape
        h_blocks, w_blocks = h // block_size, w // block_size

        all_bits = []
        for by in range(h_blocks):
            for bx in range(w_blocks):
                y1, y2 = by * block_size, (by + 1) * block_size
                x1, x2 = bx * block_size, (bx + 1) * block_size
                block = lum[y1:y2, x1:x2]
                fft_c = fft2(block)
                q = int(round(np.abs(fft_c[1, 2]) / strength))
                all_bits.append(q % 2)

        raw = np.array(all_bits, dtype=np.uint8)
        n_chunks = len(raw) // CODE_LEN
        if n_chunks == 0:
            return b'', {'bits_extracted': 0}
        parts = [bch_decode(raw[i * CODE_LEN:(i + 1) * CODE_LEN]) for i in range(n_chunks)]
        decoded = np.concatenate(parts) if parts else raw

        if len(decoded) < 16:
            return b'', {'bits_extracted': 0}
        header_bits = decoded[:16]
        data_len = struct.unpack('>H', np.packbits(header_bits.astype(np.uint8)).tobytes())[0]
        if data_len < 1 or data_len > 4096:
            return b'', {'bits_extracted': 0}
        n_needed = 16 + data_len * 8
        if len(decoded) >= n_needed:
            payload_bits = decoded[16:n_needed]
            payload = np.packbits(payload_bits.astype(np.uint8)).tobytes()
            return payload, {'bits_extracted': len(payload_bits)}
        return b'', {'bits_extracted': 0}


register(DftWatermark())
