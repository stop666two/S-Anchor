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

    def _make_pairs(self, arr: NDArray, seed: int, n_pairs: int, ps: int) -> tuple[list, list, list]:
        rng = np.random.default_rng(seed)
        h, w = arr.shape
        coords = []
        for _ in range(n_pairs * 2):
            x = rng.integers(0, w - ps)
            y = rng.integers(0, h - ps)
            coords.append((y, x))
        a_coords = coords[:n_pairs]
        b_coords = coords[n_pairs:]
        a_patches = [arr[y:y+ps, x:x+ps] for y, x in a_coords]
        b_patches = [arr[y:y+ps, x:x+ps] for y, x in b_coords]
        return a_patches, b_patches, a_coords, b_coords

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        arr = np.array(carrier.convert('RGB'), dtype=np.float64)
        arr = 0.299*arr[:,:,0] + 0.587*arr[:,:,1] + 0.114*arr[:,:,2]
        seed = params.get('seed', 42)
        strength = params.get('strength', 5.0)
        ps = 4

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        a_patches, b_patches, _, _ = self._make_pairs(arr, seed, len(bits), ps)
        for i in range(len(bits)):
            if bits[i] == 1:
                a_patches[i] += strength
                b_patches[i] -= strength
            else:
                a_patches[i] -= strength
                b_patches[i] += strength

        result = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'L').convert('RGB')
        return result, {'bits_embedded': len(bits), 'n_pairs': len(bits)}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('L'), dtype=np.float64)
        seed = params.get('seed', 42)
        ps = 4

        # Read header: first 16 pairs determine payload length
        a_patches, b_patches, _, _ = self._make_pairs(arr, seed, 16, ps)
        diffs = np.array([np.mean(a) - np.mean(b) for a, b in zip(a_patches, b_patches)])
        header_bits = (diffs > 0).astype(np.uint8)
        data_len = struct.unpack('>H', np.packbits(header_bits).tobytes())[0]
        if data_len < 1 or data_len > 4096:
            return b'', {'bits_extracted': 0}

        n_bits = 16 + data_len * 8
        a_patches, b_patches, _, _ = self._make_pairs(arr, seed, n_bits, ps)
        diffs = np.array([np.mean(a) - np.mean(b) for a, b in zip(a_patches, b_patches)])
        bits = (diffs > 0).astype(np.uint8)
        payload = np.packbits(bits[16:]).tobytes()
        return payload, {'bits_extracted': len(bits[16:])}


register(PatchworkWatermark())
