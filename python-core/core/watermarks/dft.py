import struct
import numpy as np
from PIL import Image
from numpy.typing import NDArray
from numpy.fft import fft2, ifft2, fftshift, ifftshift

from . import BaseWatermark, register


class DftWatermark(BaseWatermark):
    type_id = 'dft'
    name = 'DFT Block QIM'

    def embed_order(self) -> int:
        return 20

    def extract_order(self) -> int:
        return 50

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        rgb = np.array(carrier.convert('RGB'), dtype=np.float64)
        arr = rgb[:,:,1].copy()
        strength = params.get('strength', 200.0)
        block_size = 8

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        h, w = arr.shape
        h_blocks = h // block_size
        w_blocks = w // block_size
        n_blocks = h_blocks * w_blocks

        if len(bits) > n_blocks:
            raise ValueError(f'DFT block payload too large: {len(bits)} blocks needed, {n_blocks} available')

        modified = arr.copy()
        bi = 0
        for by in range(h_blocks):
            for bx in range(w_blocks):
                if bi >= len(bits):
                    break
                y1, y2 = by * block_size, (by + 1) * block_size
                x1, x2 = bx * block_size, (bx + 1) * block_size
                block = arr[y1:y2, x1:x2]
                fft = fft2(block)
                mag = np.abs(fft)
                # Use coefficient (1,1) - low frequency, small magnitude in block DFT
                q = int(round(mag[1, 1] / strength))
                q = (int(q / 2) * 2) | int(bits[bi])
                mag[1, 1] = max(1.0, float(q * strength))
                recon = np.real(ifft2(mag * np.exp(1j * np.angle(fft))))
                modified[y1:y2, x1:x2] = recon
                bi += 1

        rgb[:,:,1] = np.clip(modified, 0, 255)
        return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), {'bits_embedded': len(bits)}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'), dtype=np.float64)[:,:,1]
        strength = params.get('strength', 200.0)
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
                fft = fft2(block)
                mag = np.abs(fft)
                q = int(round(mag[1, 1] / strength))
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


register(DftWatermark())
