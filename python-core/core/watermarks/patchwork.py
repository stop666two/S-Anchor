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

    def _patches(self, arr: NDArray, seed: int, n_patches: int, patch_size: int) -> tuple[list, list]:
        rng = np.random.default_rng(seed)
        h, w = arr.shape
        coords = []
        for _ in range(n_patches * 2):
            x = rng.integers(0, w - patch_size)
            y = rng.integers(0, h - patch_size)
            coords.append((y, x))
        a_patches = [arr[y:y+patch_size, x:x+patch_size] for y, x in coords[:n_patches]]
        b_patches = [arr[y:y+patch_size, x:x+patch_size] for y, x in coords[n_patches:]]
        return a_patches, b_patches, coords

    def embed(self, carrier: Image.Image, payload: bytes, params: dict) -> tuple[Image.Image, dict]:
        arr = np.array(carrier.convert('L'), dtype=np.float64)
        seed = params.get('seed', 42)
        strength = params.get('strength', 1.0)
        n_patches = max(1, len(payload) * 8)
        patch_size = 4

        a_patches, b_patches, coords = self._patches(arr, seed, n_patches, patch_size)
        bits = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
        if len(bits) > n_patches:
            raise ValueError(f'Patchwork payload too large: {len(bits)} bits')

        for i in range(len(bits)):
            a_mean = np.mean(a_patches[i])
            b_mean = np.mean(b_patches[i])
            diff = abs(a_mean - b_mean)
            if bits[i] == 1:
                target_diff = diff + strength * 8
                if a_mean > b_mean:
                    a_patches[i] += target_diff / 2
                    b_patches[i] -= target_diff / 2
                else:
                    a_patches[i] -= target_diff / 2
                    b_patches[i] += target_diff / 2
            else:
                target_diff = max(0, diff - strength * 4)
                mid = (a_mean + b_mean) / 2
                a_patches[i] = np.clip(a_patches[i] - (a_mean - mid) * 0.5, 0, 255)
                b_patches[i] = np.clip(b_patches[i] - (b_mean - mid) * 0.5, 0, 255)

        result = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'L').convert('RGB')
        return result, {'bits_embedded': len(bits), 'n_patches': n_patches}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('L'), dtype=np.float64)
        seed = params.get('seed', 42)
        n_bits = params.get('n_bits', 0)
        if n_bits == 0:
            return b'', {}
        patch_size = 4
        a_patches, b_patches, _ = self._patches(arr, seed, n_bits, patch_size)
        bits = np.array([1 if np.mean(a) < np.mean(b) else 0 for a, b in zip(a_patches, b_patches)], dtype=np.uint8)
        payload = np.packbits(bits).tobytes()
        return payload, {'bits_extracted': len(bits)}


register(PatchworkWatermark())
