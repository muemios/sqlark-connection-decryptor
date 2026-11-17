"""解密原语测试：加解密回环、密钥校验、异常处理。"""

from __future__ import annotations

import base64

import pytest

from sqlark_decrypt.crypto import (
    OUTER_IV,
    OUTER_KEY,
    DecryptionError,
    _unpad,
    aes_cbc_decrypt,
    aes_cbc_encrypt,
    decrypt_outer,
    decrypt_secret,
    encrypt_outer,
    encrypt_secret,
)


def test_outer_key_and_iv_are_16_bytes() -> None:
    assert len(OUTER_KEY) == 16
    assert OUTER_IV == OUTER_KEY[::-1]


def test_outer_roundtrip() -> None:
    text = '{"host":"192.0.2.10","user":"demo"}'
    ciphertext = encrypt_outer(text)
    assert decrypt_outer(ciphertext) == text


def test_outer_ciphertext_is_stable() -> None:
    """固定 key/IV 的 CBC 是确定性加密：同样输入得到同样密文。"""
    assert encrypt_outer("demo") == encrypt_outer("demo")


def test_inner_roundtrip() -> None:
    salt = "DEMOsalt00000001"
    ciphertext = encrypt_secret("Demo#Pass123", salt)
    assert decrypt_secret(ciphertext, salt) == "Demo#Pass123"


def test_inner_without_salt_returns_input() -> None:
    assert decrypt_secret("plain-text", None) == "plain-text"
    assert decrypt_secret("plain-text", "") == "plain-text"


def test_invalid_ciphertext_length_raises() -> None:
    with pytest.raises(DecryptionError):
        aes_cbc_decrypt(b"short", OUTER_KEY, OUTER_IV)


def test_invalid_padding_raises() -> None:
    # 末字节 0x66 不是合法 PKCS5 填充
    with pytest.raises(DecryptionError):
        _unpad(b"1234567890abcdef")


def test_invalid_base64_raises() -> None:
    with pytest.raises(DecryptionError):
        decrypt_outer(base64.b64encode(b"x" * 8).decode())


def test_invalid_key_length_raises() -> None:
    with pytest.raises(ValueError):
        aes_cbc_encrypt(b"data", b"short-key", b"0123456789abcdef")


def test_encrypt_secret_requires_salt() -> None:
    with pytest.raises(ValueError):
        encrypt_secret("password", "")
