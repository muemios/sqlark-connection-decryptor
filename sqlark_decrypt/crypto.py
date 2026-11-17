"""SQLark 连接文件的双层 AES-128-CBC 加解密原语。

算法（逆向结果详见 docs/encryption.md）::

    第 1 层  整个 <connectionDetail> / <superAttr> 字段
        Base64( AES-128-CBC( JSON, key=OUTER_KEY, iv=reverse(OUTER_KEY), PKCS5 ) )

    第 2 层  JSON 内的 password / sshPassword / sslPassword 字段
        Base64( AES-128-CBC( 明文, key=salt, iv=reverse(salt), PKCS5 ) )

``salt`` 是每条连接随机生成的 16 位字符串，与密文一起保存在 JSON 中。

本模块只负责“字节 <-> 密文”的转换，不涉及 XML 和业务字段；方便单独测试。
"""

from __future__ import annotations

import base64
from typing import Optional, Union

try:  # pragma: no cover - 依赖缺失时的友好提示在 CLI 中处理
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "缺少 cryptography 依赖，请先执行: pip install cryptography"
    ) from exc

#: 第 1 层使用的全局密钥（SQLark 硬编码常量，SysConnectionInfoConstant.SALT）
OUTER_KEY = b"fudih4xp113znwp7"

#: 第 1 层使用的 IV —— 代码中对密钥做了字符串反转
OUTER_IV = OUTER_KEY[::-1]

_BLOCK_SIZE = 16
BytesLike = Union[bytes, bytearray]


class DecryptionError(ValueError):
    """密文无法解密（密钥/IV 不匹配、Base64 损坏、填充非法等）。"""


def _ensure_bytes(value: Union[str, BytesLike], name: str) -> bytes:
    if isinstance(value, str):
        value = value.encode("utf-8")
    if len(value) != _BLOCK_SIZE:
        raise ValueError(f"{name} 必须为 {_BLOCK_SIZE} 字节，实际 {len(value)} 字节")
    return bytes(value)


def _unpad(data: bytes) -> bytes:
    """去除 PKCS#5/PKCS#7 填充，并校验填充合法性。"""
    if not data:
        raise DecryptionError("解密结果为空")
    pad = data[-1]
    if not 1 <= pad <= _BLOCK_SIZE or data[-pad:] != bytes([pad]) * pad:
        raise DecryptionError("PKCS5 填充校验失败，密钥/IV 或密文有误")
    return data[:-pad]


def _pad(data: bytes) -> bytes:
    padder = padding.PKCS7(_BLOCK_SIZE * 8).padder()
    return padder.update(data) + padder.finalize()


def aes_cbc_decrypt(ciphertext: bytes, key: Union[str, BytesLike], iv: Union[str, BytesLike]) -> bytes:
    """AES-CBC/PKCS5 解密，返回去填充后的原始字节。"""
    key_b, iv_b = _ensure_bytes(key, "key"), _ensure_bytes(iv, "iv")
    if len(ciphertext) == 0 or len(ciphertext) % _BLOCK_SIZE != 0:
        raise DecryptionError("密文长度必须是 16 的整数倍")
    decryptor = Cipher(algorithms.AES(key_b), modes.CBC(iv_b)).decryptor()
    try:
        plain = decryptor.update(ciphertext) + decryptor.finalize()
    except ValueError as exc:  # cryptography 对非法长度抛出 ValueError
        raise DecryptionError(str(exc)) from exc
    return _unpad(plain)


def aes_cbc_encrypt(plain: bytes, key: Union[str, BytesLike], iv: Union[str, BytesLike]) -> bytes:
    """AES-CBC/PKCS5 加密，返回密文字节。"""
    key_b, iv_b = _ensure_bytes(key, "key"), _ensure_bytes(iv, "iv")
    encryptor = Cipher(algorithms.AES(key_b), modes.CBC(iv_b)).encryptor()
    return encryptor.update(_pad(plain)) + encryptor.finalize()


def decrypt_base64(
    ciphertext_b64: str, key: Union[str, BytesLike], iv: Union[str, BytesLike]
) -> str:
    """Base64 密文 -> 明文字符串（UTF-8）。"""
    try:
        ciphertext = base64.b64decode(ciphertext_b64, validate=False)
    except (ValueError, TypeError) as exc:
        raise DecryptionError(f"Base64 解码失败: {exc}") from exc
    return aes_cbc_decrypt(ciphertext, key, iv).decode("utf-8")


def encrypt_base64(plain: str, key: Union[str, BytesLike], iv: Union[str, BytesLike]) -> str:
    """明文字符串 -> Base64 密文。"""
    return base64.b64encode(aes_cbc_encrypt(plain.encode("utf-8"), key, iv)).decode("ascii")


def decrypt_outer(ciphertext_b64: str) -> str:
    """第 1 层：解密整个 ``<connectionDetail>`` / ``<superAttr>`` 字段。"""
    return decrypt_base64(ciphertext_b64, OUTER_KEY, OUTER_IV)


def encrypt_outer(json_text: str) -> str:
    """第 1 层：加密整个字段（用于重新生成连接文件）。"""
    return encrypt_base64(json_text, OUTER_KEY, OUTER_IV)


def decrypt_secret(ciphertext_b64: str, salt: Optional[str]) -> str:
    """第 2 层：解密密码字段。

    Args:
        ciphertext_b64: JSON 中 ``password`` 等字段的值。
        salt: 同一条记录里的 ``salt``；为空时说明该字段未加密，原样返回。

    Returns:
        明文密码；``salt`` 为空时返回原值。
    """
    if not ciphertext_b64 or not salt:
        return ciphertext_b64
    return decrypt_base64(ciphertext_b64, salt, salt[::-1])


def encrypt_secret(plain: str, salt: str) -> str:
    """第 2 层：加密密码字段（用于改写连接文件）。"""
    if not salt:
        raise ValueError("salt 不能为空")
    return encrypt_base64(plain, salt, salt[::-1])
