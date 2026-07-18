import pytest
import numpy as np
from PIL import Image
from core.config import WatermarkConfig
from core.watermark import embed_watermark, extract_watermark


def _image(size=(256, 256)):
    arr = np.random.randint(0, 256, (*size, 3), dtype=np.uint8)
    return Image.fromarray(arr, 'RGB')


def test_long_watermark_raises_error():
    img = _image((256, 256))
    long_text = b'dcbsx csxc  nfc  fazcsvc  sc'
    config = WatermarkConfig(alpha=0.05, delta=36.0, level=1, sync_enabled=True, bch_enabled=True)
    with pytest.raises(ValueError, match='Watermark too long'):
        embed_watermark(img, long_text, config)


def test_long_watermark_no_bch_raises_error():
    img = _image((128, 128))
    long_text = b'dcbsx csxc  nfc  fazcsvc  sc'
    config = WatermarkConfig(alpha=0.05, delta=36.0, level=1, sync_enabled=False, bch_enabled=False)
    with pytest.raises(ValueError, match='Watermark too long'):
        embed_watermark(img, long_text, config)


def test_short_watermark_ok():
    img = _image((256, 256))
    config = WatermarkConfig(alpha=0.05, delta=36.0, level=1, sync_enabled=True, bch_enabled=True)
    result, _ = embed_watermark(img, b'dcbsx csxc', config)
    extracted, _ = extract_watermark(result, config)
    assert b'dcbsx csxc' in extracted
