import numpy as np
from core.metrics import psnr, ssim


def test_psnr_identical():
    img = np.ones((8, 8, 3), dtype=np.uint8) * 128
    assert psnr(img, img) == float('inf')


def test_psnr_different():
    a = np.zeros((8, 8, 3), dtype=np.uint8)
    b = np.ones((8, 8, 3), dtype=np.uint8) * 255
    p = psnr(a, b)
    assert p == 0.0


def test_ssim_identical():
    img = np.ones((8, 8), dtype=np.float64) * 128
    assert abs(ssim(img, img) - 1.0) < 1e-6


def test_ssim_different():
    a = np.zeros((8, 8), dtype=np.float64)
    b = np.ones((8, 8), dtype=np.float64) * 255
    s = ssim(a, b)
    assert 0 < s < 1
