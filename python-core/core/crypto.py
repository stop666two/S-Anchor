import os
import hashlib
import hmac

MAGIC = b'ENC!'  # 4-byte magic marker


def derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=32)


def is_encrypted(data: bytes) -> bool:
    """Check if data starts with the encryption magic marker."""
    return len(data) >= 4 and data[:4] == MAGIC


def encrypt(plaintext: bytes, password: str) -> bytes:
    if not password:
        return plaintext
    salt = os.urandom(16)
    key = derive_key(password, salt)
    iv = os.urandom(16)
    prng = hashlib.sha256(iv + key).digest()
    needed = len(plaintext)
    while len(prng) < needed:
        prng += hashlib.sha256(prng[-32:] + key).digest()
    keystream = prng[:needed]
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, keystream))
    mac = hmac.new(key, iv + ciphertext, 'sha256').digest()[:8]
    return MAGIC + salt + iv + mac + ciphertext


def decrypt(data: bytes, password: str) -> bytes:
    if not password:
        return data
    if not is_encrypted(data):
        return data
    salt, iv, mac, ciphertext = data[4:20], data[20:36], data[36:44], data[44:]
    key = derive_key(password, salt)
    expected_mac = hmac.new(key, iv + ciphertext, 'sha256').digest()[:8]
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError('Incorrect password or corrupted data')
    prng = hashlib.sha256(iv + key).digest()
    needed = len(ciphertext)
    while len(prng) < needed:
        prng += hashlib.sha256(prng[-32:] + key).digest()
    keystream = prng[:needed]
    return bytes(a ^ b for a, b in zip(ciphertext, keystream))
