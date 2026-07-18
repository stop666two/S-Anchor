from PIL import Image

from .watermarks import WatermarkSpec, get, sorted_for_embed, sorted_for_extract
from .crypto import encrypt, decrypt, is_encrypted


def run_embed(carrier: Image.Image, specs: list[WatermarkSpec]) -> tuple[Image.Image, list[dict]]:
    result = carrier
    results = []
    for spec in sorted(specs, key=lambda s: _order(s.type)):
        wm = get(spec.type)
        if wm is None:
            raise ValueError(f'Unknown watermark type: {spec.type}')
        payload = spec.text.encode('utf-8') if spec.text else b'\x00'
        params = dict(spec.params or {})
        password = params.pop('password', '')
        if password:
            payload = encrypt(payload, password)
        result, meta = wm.embed(result, payload, params)
        results.append({'type': spec.type, **meta})
    return result, results


def run_extract(stego: Image.Image, specs: list[WatermarkSpec]) -> list[dict]:
    results = []
    for spec in sorted(specs, key=lambda s: _order(s.type, extract=True)):
        wm = get(spec.type)
        if wm is None:
            raise ValueError(f'Unknown watermark type: {spec.type}')
        params = dict(spec.params or {})
        password = params.pop('password', '')
        payload, meta = wm.extract(stego, params)
        if is_encrypted(payload):
            if password:
                try:
                    payload = decrypt(payload, password)
                except ValueError:
                    payload = b''
                    meta['decrypt_error'] = 'wrong password'
            else:
                meta['needs_password'] = True
                payload = b''
        text = payload.decode('utf-8', errors='replace')
        results.append({'type': spec.type, 'text': text, **meta})
    return results


def _order(type_id: str, extract: bool = False) -> int:
    wm = get(type_id)
    if wm is None:
        return 50
    return wm.extract_order() if extract else wm.embed_order()
