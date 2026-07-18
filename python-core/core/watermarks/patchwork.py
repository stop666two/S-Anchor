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

    def _patches(self, arr: NDArray, seed: int, n_patches: int, patch_size: int) -> tuple:
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
        patch_size = 4

        length_bytes = struct.pack('>H', len(payload))
        data = length_bytes + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))
        n_patches = max(1, len(bits))

        a_patches, b_patches, coords = self._patches(arr, seed, n_patches, patch_size)
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
                mid = (a_mean + b_mean) / 2
                target_diff = max(0, diff - strength * 4)
                a_patches[i] = np.clip(a_patches[i] - (a_mean - mid) * 0.5, 0, 255)
                b_patches[i] = np.clip(b_patches[i] - (b_mean - mid) * 0.5, 0, 255)

        result = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'L').convert('RGB')
        return result, {'bits_embedded': len(bits), 'n_patches': n_patches}

    def extract(self, stego: Image.Image, params: dict) -> tuple[bytes, dict]:
        arr = np.array(stego.convert('L'), dtype=np.float64)
        seed = params.get('seed', 42)
        patch_size = 4
        total_pixels = arr.size

        # Need at least 16 patches for header (8 pixel pairs = 16 patches)
        min_patches = 16
        coord_pixels_needed = min_patches * 2 * patch_size * patch_size
        if total_pixels < coord_pixels_needed:
            return b'', {'bits_extracted': 0}

        a_patches, b_patches, _ = self._patches(arr, seed, min_patches, patch_size)
        header_bits = np.array([1 if np.mean(a) < np.mean(b) else 0 for a, b in zip(a_patches, b_patches)], dtype=np.uint8)
        data_len = struct.unpack('>H', np.packbits(header_bits).tobytes())[0]
        if data_len < 1 or data_len > 4096:
            return b'', {'bits_extracted': 0}

        n_bits = 16 + data_len * 8
        max_patches = min(n_bits, total_pixels // (2 * patch_size * patch_size))
        if max_patches < n_bits:
            return b'', {'bits_extracted': 0}

        a_patches, b_patches, _ = self._patches(arr, seed, n_bits, patch_size)
        bits = np.array([1 if np.mean(a) < np.mean(b) else 0 for a, b in zip(a_patches, b_patches)], dtype=np.uint8)
        payload_bits = bits[16:]
        payload = np.packbits(payload_bits).tobytes()
        return payload, {'bits_extracted': len(payload_bits)}


register(PatchworkWatermark())
