import numpy as np
from PIL import Image
from core.config import WatermarkConfig
from core.watermark import embed_watermark, extract_watermark


def _image(size=(256, 256)):
    arr = np.random.randint(0, 256, (*size, 3), dtype=np.uint8)
    return Image.fromarray(arr, 'RGB')


def test_embed_extract_roundtrip():
    img = _image((256, 256))
    data = b'S-ANCHOR'
    config = WatermarkConfig(alpha=0.05, delta=36.0, level=2, sync_enabled=True, bch_enabled=True)
    result, metrics = embed_watermark(img, data, config)
    assert result.size == img.size
    assert metrics['psnr'] > 25
    assert metrics['ssim'] > 0.9
    extracted, info = extract_watermark(result, config)
    assert data in extracted


def test_embed_extract_no_bch():
    img = _image((128, 128))
    data = b'TEST'
    config = WatermarkConfig(alpha=0.05, delta=36.0, level=1, sync_enabled=False, bch_enabled=False)
    result, metrics = embed_watermark(img, data, config)
    assert result.size == img.size
    assert metrics['psnr'] > 10
    extracted, info = extract_watermark(result, config)
    assert len(extracted) > 0


def test_embed_extract_no_sync():
    img = _image((256, 256))
    data = b'HELLO'
    config = WatermarkConfig(alpha=0.05, delta=36.0, level=2, sync_enabled=False, bch_enabled=True)
    result, _ = embed_watermark(img, data, config)
    extracted, info = extract_watermark(result, config)
    assert data in extracted
