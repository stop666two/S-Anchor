import struct
import numpy as np
from PIL import Image
from numpy.typing import NDArray
from numpy.fft import fft2, ifft2

from . import BaseWatermark, register


class DftWatermark(BaseWatermark):
    type_id = 'dft'
    name = 'DFT Magnitude QIM'

    def embed_order(self) -> int:
        return 20

    def extract_order(self) -> int:
        return 50

    def _mid_ring(self, h: int, w: int, r_min: float, r_max: float) -> NDArray:
        cy, cx = h // 2, w // 2
        y, x = np.ogrid[:h, :w]
        r = np.sqrt((y - cy)**2 + (x - cx)**2)
        return (r >= r_min) & (r <= r_max)

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        rgb = np.array(carrier.convert('RGB'), dtype=np.float64)
        arr = rgb[:,:,1].copy()
        strength = params.get('strength', 8.0)
        r_min = params.get('r_min', 0.15)
        r_max = params.get('r_max', 0.35)

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        h, w = arr.shape
        mask = self._mid_ring(h, w, r_min * min(h, w) / 2, r_max * min(h, w) / 2)
        positions = np.argwhere(mask)
        if len(bits) > len(positions):
            raise ValueError(f'DFT payload too large')

        fft = fft2(arr)
        mag = np.abs(fft)
        phase = np.angle(fft)

        for i in range(len(bits)):
            y, x = positions[i]
            q = int(round(mag[y, x] / strength))
            target = float((int(q / 2) * 2 + int(bits[i])) * strength)
            mag[y, x] = target

        fft_mod = mag * np.exp(1j * phase)
        recon = np.real(ifft2(fft_mod))
        # Apply delta with clipping protection
        delta = recon - arr
        delta = np.clip(delta, -255, 255)
        rgb[:,:,1] += delta
        return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), 'RGB'), {'bits_embedded': len(bits)}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'), dtype=np.float64)[:,:,1]
        h, w = arr.shape
        strength = params.get('strength', 8.0)
        r_min = params.get('r_min', 0.15)
        r_max = params.get('r_max', 0.35)

        fft = fft2(arr)
        mag = np.abs(fft)
        mask = self._mid_ring(h, w, r_min * min(h, w) / 2, r_max * min(h, w) / 2)
        positions = np.argwhere(mask)
        if len(positions) < 16:
            return b'', {'bits_extracted': 0}

        bits = []
        for i in range(min(16, len(positions))):
            y, x = positions[i]
            q = int(round(mag[y, x] / strength))
            bits.append(q % 2)

        header_bits = np.array(bits[:16], dtype=np.uint8)
        data_len = struct.unpack('>H', np.packbits(header_bits).tobytes())[0]
        if data_len < 1 or data_len > 4096:
            return b'', {'bits_extracted': 0}

        n_bits = 16 + data_len * 8
        n_bits = min(n_bits, len(positions))
        bits = np.zeros(n_bits - 16, dtype=np.uint8)
        for i in range(16, n_bits):
            y, x = positions[i]
            q = int(round(mag[y, x] / strength))
            bits[i - 16] = q % 2

        payload = np.packbits(bits).tobytes()
        return payload, {'bits_extracted': len(bits)}


register(DftWatermark())
