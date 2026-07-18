import numpy as np
from PIL import Image
from numpy.typing import NDArray
from numpy.fft import fft2, ifft2

from . import BaseWatermark, register


class DftWatermark(BaseWatermark):
    type_id = 'dft'
    name = 'DFT Phase Modulation'

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
        arr = np.array(carrier.convert('L'), dtype=np.float64)
        strength = params.get('strength', 15.0)
        r_min = params.get('r_min', 0.15)
        r_max = params.get('r_max', 0.35)

        fft = fft2(arr)
        phase = np.angle(fft)
        mag = np.abs(fft)
        h, w = arr.shape

        bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
        mask = self._mid_ring(h, w, r_min * min(h, w) / 2, r_max * min(h, w) / 2)
        positions = np.argwhere(mask)
        if len(bits) > len(positions):
            raise ValueError(f'DFT payload too large: {len(bits)} bits, max {len(positions)}')

        delta = np.pi / 2
        for i in range(len(bits)):
            y, x = positions[i]
            if bits[i] == 1:
                phase[y, x] = delta
            else:
                phase[y, x] = -delta

        fft_modified = mag * np.exp(1j * phase)
        result = np.real(ifft2(fft_modified)).clip(0, 255).astype(np.uint8)
        return Image.fromarray(result, 'L').convert('RGB'), {'bits_embedded': len(bits)}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('L'), dtype=np.float64)
        h, w = arr.shape
        r_min = params.get('r_min', 0.15)
        r_max = params.get('r_max', 0.35)
        n_bits = params.get('n_bits', 0)
        if n_bits == 0:
            return b'', {}

        fft = fft2(arr)
        phase = np.angle(fft)
        mask = self._mid_ring(h, w, r_min * min(h, w) / 2, r_max * min(h, w) / 2)
        positions = np.argwhere(mask)
        n_bits = min(n_bits, len(positions))

        bits = np.zeros(n_bits, dtype=np.uint8)
        for i in range(n_bits):
            y, x = positions[i]
            bits[i] = 1 if phase[y, x] > 0 else 0

        payload = np.packbits(bits).tobytes()
        return payload, {'bits_extracted': n_bits}


register(DftWatermark())
