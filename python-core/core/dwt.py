import numpy as np
import pywt


def decompose_y_channel(y_channel: np.ndarray, level: int = 2) -> dict:
    coeffs = pywt.wavedec2(y_channel, 'haar', level=level)
    result = {'LL': coeffs[0]}
    for i in range(1, level + 1):
        result[f'LH{i}'] = coeffs[i][0]
        result[f'HL{i}'] = coeffs[i][1]
        result[f'HH{i}'] = coeffs[i][2]
    return result


def reconstruct_from_ll(modified_ll: np.ndarray, original_coeffs: list, level: int = 2) -> np.ndarray:
    coeffs = [modified_ll]
    for i in range(1, level + 1):
        coeffs.append((
            original_coeffs[i][0],
            original_coeffs[i][1],
            original_coeffs[i][2]
        ))
    return pywt.waverec2(coeffs, 'haar')


def get_full_coeffs(y_channel: np.ndarray, level: int = 2) -> list:
    return list(pywt.wavedec2(y_channel, 'haar', level=level))
