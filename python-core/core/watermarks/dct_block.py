import struct

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from scipy.fft import dct, idct

from ..bch_codec import CODE_LEN, DATA_LEN
from ..bch_codec import decode as bch_decode
from ..bch_codec import encode as bch_encode
from . import BaseWatermark, register


class DctBlockWatermark(BaseWatermark):
    type_id = 'dct_block'
    name = 'DCT Block (JPEG-robust)'

    def embed_order(self) -> int:
        return 15

    def extract_order(self) -> int:
        return 55

    def _dct_2d(self, block: NDArray) -> NDArray:
        return dct(dct(block, axis=0, norm='ortho'), axis=1, norm='ortho')

    def _idct_2d(self, coeff: NDArray) -> NDArray:
        return idct(idct(coeff, axis=0, norm='ortho'), axis=1, norm='ortho')

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        arr = np.array(carrier.convert('RGB'), dtype=np.float64)
        arr = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
        h, w = arr.shape
        strength = params.get('strength', 18.0)
        block_size = 8

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        raw_bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        n_bch = max(1, (len(raw_bits) + DATA_LEN - 1) // DATA_LEN)
        raw_bits = np.pad(raw_bits, (0, n_bch * DATA_LEN - len(raw_bits)), 'constant')
        chunks = [bch_encode(raw_bits[i * DATA_LEN:(i + 1) * DATA_LEN]) for i in range(n_bch)]
        bits = np.concatenate(chunks)
        n_data = len(bits)

        h_blocks = h // block_size
        w_blocks = w // block_size
        n_blocks = h_blocks * w_blocks

        if n_data > n_blocks:
            raise ValueError(f'DCT block payload too large: need {n_data} blocks, only {n_blocks} available')

        modified = arr.copy()
        bi = 0
        for by in range(h_blocks):
            for bx in range(w_blocks):
                if bi >= n_data:
                    break
                block = arr[by*block_size:(by+1)*block_size, bx*block_size:(bx+1)*block_size]
                dct_block = self._dct_2d(block)
                mid = float(dct_block[4, 1])  # mid-frequency coefficient
                q = int(round(mid / strength))
                if bi < len(bits):
                    target = float((int(q / 2) * 2) * strength + (int(bits[bi]) * strength))
                else:
                    target = float(q * strength)
                dct_block[4, 1] = target
                modified[by*block_size:(by+1)*block_size, bx*block_size:(bx+1)*block_size] = self._idct_2d(dct_block)
                bi += 1

        result_clipped = np.clip(modified, 0, 255)
        result_rgb = np.array(carrier.convert('RGB'), dtype=np.float64)
        y = 0.299*result_rgb[:,:,0] + 0.587*result_rgb[:,:,1] + 0.114*result_rgb[:,:,2]
        dy = result_clipped - y
        for c in range(3):
            result_rgb[:,:,c] += dy
        return Image.fromarray(np.clip(result_rgb, 0, 255).astype(np.uint8), 'RGB'), {'bits_embedded': n_data}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'), dtype=np.float64)
        arr = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
        h, w = arr.shape
        strength = params.get('strength', 18.0)
        block_size = 8
        h_blocks = h // block_size
        w_blocks = w // block_size

        all_bits = []
        for by in range(h_blocks):
            for bx in range(w_blocks):
                block = arr[by*block_size:(by+1)*block_size, bx*block_size:(bx+1)*block_size]
                dct_block = self._dct_2d(block)
                q = round(dct_block[4, 1] / strength)
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


register(DctBlockWatermark())
