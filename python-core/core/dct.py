import numpy as np
from numpy.typing import NDArray
from scipy.fft import dct, idct

BLOCK_SIZE = 8


def block_split(matrix: NDArray) -> NDArray:
    h, w = matrix.shape
    h_blocks = h // BLOCK_SIZE
    w_blocks = w // BLOCK_SIZE
    matrix = matrix[:h_blocks * BLOCK_SIZE, :w_blocks * BLOCK_SIZE]
    blocks = matrix.reshape(h_blocks, BLOCK_SIZE, w_blocks, BLOCK_SIZE)
    blocks = blocks.transpose(0, 2, 1, 3)
    return blocks.reshape(-1, BLOCK_SIZE, BLOCK_SIZE)


def block_merge(blocks: NDArray, original_shape: tuple[int, int]) -> NDArray:
    h, w = original_shape
    h_blocks = h // BLOCK_SIZE
    w_blocks = w // BLOCK_SIZE
    blocks = blocks.reshape(h_blocks, w_blocks, BLOCK_SIZE, BLOCK_SIZE)
    blocks = blocks.transpose(0, 2, 1, 3)
    return blocks.reshape(h_blocks * BLOCK_SIZE, w_blocks * BLOCK_SIZE)


def dct_2d(block: NDArray) -> NDArray:
    return dct(dct(block, axis=0, norm='ortho'), axis=1, norm='ortho')


def idct_2d(coeff: NDArray) -> NDArray:
    return idct(idct(coeff, axis=0, norm='ortho'), axis=1, norm='ortho')


def dct_blockwise(matrix: NDArray) -> tuple[NDArray, tuple[int, int]]:
    blocks = block_split(matrix)
    dct_blocks = np.array([dct_2d(b) for b in blocks])
    return dct_blocks, matrix.shape


def idct_blockwise(dct_blocks: NDArray, original_shape: tuple[int, int]) -> NDArray:
    idct_blocks = np.array([idct_2d(b) for b in dct_blocks])
    return block_merge(idct_blocks, original_shape)
