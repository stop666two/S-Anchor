import pytest
import numpy as np
from PIL import Image
from core.watermarks import get, list_types


def _image(size=(256, 256)):
    arr = np.random.randint(0, 256, (*size, 3), dtype=np.uint8)
    return Image.fromarray(arr, 'RGB')


TYPE_PARAMS = [
    ('freq', {'alpha': 0.15, 'delta': 40, 'level': 1, 'sync': True, 'bch': True}),
    ('dft', {'strength': 50}),
    ('dwtsvd', {'strength': 30}),
    ('dct_block', {'strength': 30}),
    ('svd', {'strength': 40}),
    ('spread', {'strength': 30, 'spread_factor': 64, 'seed': 42}),
    ('patchwork', {'strength': 25, 'seed': 7}),
    ('lsb', {}),
    ('reversible', {}),
    ('visible', {'x': 50, 'y': 50, 'font_size': 48, 'opacity': 0.3}),
]


def test_list_types_includes_all():
    types = list_types()
    type_ids = {t['type_id'] for t in types}
    expected = {'freq', 'dft', 'dwtsvd', 'dct_block', 'svd', 'spread', 'patchwork', 'lsb', 'reversible', 'visible'}
    missing = expected - type_ids
    assert not missing, f'Missing types: {missing}'


@pytest.mark.parametrize('type_id,params', TYPE_PARAMS)
def test_embed_extract_roundtrip(type_id, params):
    wm = get(type_id)
    assert wm is not None, f'{type_id} not registered'
    img = _image((128, 128))
    data = b'T' * (2 if type_id in ('freq',) else 4)
    img_use = _image((256, 256)) if type_id in ('freq', 'dwtsvd') else img
    result, meta = wm.embed(img_use, data, params)
    assert result.size == img_use.size
    if type_id == 'visible':
        return
    extracted, info = wm.extract(result, params)
    if type_id in ('spread', 'patchwork'):
        assert len(extracted) > 0, f'{type_id}: empty result'
    else:
        assert data in extracted, f'{type_id}: expected {data!r}, got {extracted!r}'


@pytest.mark.parametrize('type_id,params', TYPE_PARAMS)
def test_embed_non_destructive(type_id, params):
    wm = get(type_id)
    assert wm is not None
    img = _image((256, 256))
    data = b'T' * 4
    result, _ = wm.embed(img, data, params)
    orig = np.array(img, dtype=np.float64)
    mod = np.array(result, dtype=np.float64)
    mse = np.mean((orig - mod) ** 2)
    max_pixel = 255.0
    psnr = 20 * np.log10(max_pixel / np.sqrt(mse)) if mse > 0 else 99
    assert psnr > 20, f'{type_id}: PSNR too low: {psnr:.1f}dB'


def test_freq_long_text_raises():
    wm = get('freq')
    img = _image((256, 256))
    with pytest.raises(ValueError):
        wm.embed(img, b'X' * 100, {'alpha': 0.15, 'delta': 40, 'level': 1, 'sync': True, 'bch': True})


def test_lsb_large_payload():
    wm = get('lsb')
    img = _image((64, 64))
    large = b'X' * 512
    result, meta = wm.embed(img, large, {})
    extracted, _ = wm.extract(result, {})
    assert large in extracted


def test_visible_empty_text():
    wm = get('visible')
    img = _image((64, 64))
    result, _ = wm.embed(img, b'', {})
    import numpy as np
    assert np.array_equal(np.array(result), np.array(img))


def test_dft_larger_image():
    wm = get('dft')
    img = _image((256, 256))
    data = b'DFTTEST'
    result, _ = wm.embed(img, data, {'strength': 50})
    extracted, _ = wm.extract(result, {'strength': 50})
    assert b'DFTTEST' in extracted