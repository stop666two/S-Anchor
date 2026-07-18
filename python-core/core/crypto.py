import os
import hashlib
import hmac

MAGIC = b'EN'  # 2-byte magic marker


def derive_key(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000, dklen=32)


def is_encrypted(data: bytes) -> bool:
    return len(data) >= 2 and data[:2] == MAGIC


def encrypt(plaintext: bytes, password: str) -> bytes:
    if not password:
        return plaintext
    salt = os.urandom(8)
    key = derive_key(password, salt)
    iv = os.urandom(8)
    prng = hashlib.sha256(iv + key).digest()
    needed = len(plaintext)
    while len(prng) < needed:
        prng += hashlib.sha256(prng[-32:] + key).digest()
    keystream = prng[:needed]
    ciphertext = bytes(a ^ b for a, b in zip(plaintext, keystream))
    mac = hmac.new(key, iv + ciphertext, 'sha256').digest()[:4]
    return MAGIC + salt + iv + mac + ciphertext


def decrypt(data: bytes, password: str) -> bytes:
    if not password:
        return data
    if not is_encrypted(data):
        return data
    if len(data) < 22:
        return data
    salt, iv, mac, ciphertext = data[2:10], data[10:18], data[18:22], data[22:]
    key = derive_key(password, salt)
    expected_mac = hmac.new(key, iv + ciphertext, 'sha256').digest()[:4]
    if not hmac.compare_digest(mac, expected_mac):
        raise ValueError('Incorrect password or corrupted data')
    prng = hashlib.sha256(iv + key).digest()
    needed = len(ciphertext)
    while len(prng) < needed:
        prng += hashlib.sha256(prng[-32:] + key).digest()
    keystream = prng[:needed]
    return bytes(a ^ b for a, b in zip(ciphertext, keystream))
