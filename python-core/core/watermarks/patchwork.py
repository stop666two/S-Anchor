import struct
import numpy as np
from PIL import Image
from numpy.typing import NDArray

from . import BaseWatermark, register


class PatchworkWatermark(BaseWatermark):
    type_id = 'patchwork'
    name = 'Statistical Patchwork'

    def embed_order(self) -> int:
        return 40

    def extract_order(self) -> int:
        return 30

    def _split_patch(self, arr: NDArray, seed: int, n_patches: int, ps: int):
        """Generate split patches (left/right half of same region)."""
        rng = np.random.default_rng(seed)
        h, w = arr.shape
        coords = []
        for _ in range(n_patches):
            x = rng.integers(0, w - ps * 2)
            y = rng.integers(0, h - ps)
            coords.append((y, x))
        lefts = [arr[y:y+ps, x:x+ps] for y, x in coords]
        rights = [arr[y:y+ps, x+ps:x+ps*2] for y, x in coords]
        return lefts, rights

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        arr = np.array(carrier.convert('RGB'), dtype=np.float64)
        lum = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
        seed = params.get('seed', 42)
        strength = params.get('strength', 25.0)
        ps = 4  # patch half-size

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        lefts, rights = self._split_patch(lum, seed, len(bits), ps)
        for i in range(len(bits)):
            if bits[i] == 1:
                lefts[i] += strength
                rights[i] -= strength
            else:
                lefts[i] -= strength
                rights[i] += strength

        # Apply luminance change to all channels equally
        dy = lum - (0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2])
        for c in range(3):
            arr[:,:,c] += dy

        result = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(result, 'RGB'), {'bits_embedded': len(bits)}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('RGB'), dtype=np.float64)
        lum = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
        seed = params.get('seed', 42)
        ps = 4

        lefts, rights = self._split_patch(lum, seed, 16, ps)
        diffs = np.array([np.mean(l) - np.mean(r) for l, r in zip(lefts, rights)])
        header_bits = (diffs > 0).astype(np.uint8)
        data_len = struct.unpack('>H', np.packbits(header_bits).tobytes())[0]
        if data_len < 1 or data_len > 4096:
            return b'', {'bits_extracted': 0}

        n_bits = 16 + data_len * 8
        lefts, rights = self._split_patch(lum, seed, n_bits, ps)
        diffs = np.array([np.mean(l) - np.mean(r) for l, r in zip(lefts, rights)])
        bits = (diffs > 0).astype(np.uint8)
        payload = np.packbits(bits[16:]).tobytes()
        return payload, {'bits_extracted': len(bits[16:])}


register(PatchworkWatermark())
