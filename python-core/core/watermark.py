from PIL import Image

from .config import WatermarkConfig
from .watermarks.freq import FreqWatermark
from .watermarks import get

_freq = FreqWatermark()


def embed_watermark(carrier: Image.Image, watermark_data: bytes, config: WatermarkConfig | None = None) -> tuple[Image.Image, dict]:
    if config is None:
        config = WatermarkConfig()
    params = {
        'alpha': config.alpha,
        'delta': config.delta,
        'level': config.level,
        'sync': config.sync_enabled,
        'bch': config.bch_enabled,
    }
    return _freq.embed(carrier, watermark_data, params)


def extract_watermark(stego: Image.Image, config: WatermarkConfig | None = None) -> tuple[bytes, dict]:
    if config is None:
        config = WatermarkConfig()
    params = {
        'delta': config.delta,
        'level': config.level,
        'sync': config.sync_enabled,
        'bch': config.bch_enabled,
    }
    return _freq.extract(stego, params)


def calc_capacity(img_w: int, img_h: int, config: WatermarkConfig) -> dict:
    from .bch_codec import CODE_LEN, DATA_LEN
    needed = 64 + 64
    if config.bch_enabled:
        needed = ((needed + 6) // 7) * 15 + 64
    level = config.level
    for lv in range(level, 0, -1):
        d = 8 * (2 ** lv)
        w = (img_w // d) * d
        h = (img_h // d) * d
        if w < d or h < d:
            continue
        blocks = (w // (8 << lv)) * (h // (8 << lv))
        if blocks >= needed:
            level = lv
            break
    else:
        level = 1

    divisor = 8 * (1 << level)
    w = (img_w // divisor) * divisor
    h = (img_h // divisor) * divisor
    blocks = (w // (8 << level)) * (h // (8 << level))
    n_sync = 64 if config.sync_enabled else 0
    avail = blocks - n_sync
    if avail < 8:
        return {'level': level, 'blocks': blocks, 'max_bytes': 0, 'note': 'image too small'}
    if config.bch_enabled:
        n_bch = max(1, avail // CODE_LEN)
        max_bytes = max(1, n_bch * DATA_LEN // 8)
    else:
        max_bytes = max(1, min(avail, 512) // 8)
    return {'level': level, 'blocks': blocks, 'max_bytes': max_bytes}
