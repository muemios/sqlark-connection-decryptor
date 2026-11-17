# SQLark 连接文件加密原理

本文记录 `connectionInfo.xml` / `connection-server.xml` 中连接信息的加密方式。
所有示例数据均为虚构（主机使用 RFC 5737 文档专用网段，密码为演示值）。

## 1. 结论

SQLark 对连接信息使用**两层 AES-128-CBC（PKCS5Padding）**：

| 层级 | 加密对象 | Key | IV | 输出 |
| --- | --- | --- | --- | --- |
| 第 1 层 | 整个 `<connectionDetail>` / `<superAttr>` / `<sshDetail>` / `<sslDetail>` 字段 | `fudih4xp113znwp7`（硬编码） | `reverse(key)` = `7pwnz311px4hiduf` | Base64，再做 XML 转义 |
| 第 2 层 | JSON 内的 `password` / `sshPassword` / `sslPassword` / `passphrase` | 该连接的 `salt`（16 位随机串） | `reverse(salt)` | Base64 |

`<connectionName>` / `<host>` / `<port>` / `<userName>` / `<dbType>` 等外层字段是明文，
只有连接详情 JSON 与其中的密码字段被加密。

## 2. 加密的数据结构

以演示连接为例，解密第 1 层后得到如下 JSON（节选）：

```json
{
  "dbType": "ORACLE",
  "host": "192.0.2.10",
  "port": 1521,
  "user": "demo_user",
  "password": "h5bfBSGfDGiAZwyZZGSFeg==",
  "salt": "DEMOsalt00000001",
  "connectWay": "url",
  "url": "jdbc:oracle:thin:@192.0.2.10:1521/DEMO",
  "sshOpen": false,
  "sslOpen": false,
  "rememberPassword": true
}
```

- `password` 是第 2 层密文；
- `salt` 是生成该密文时使用的随机盐，**与密文一起保存**；
- 解密顺序：先解第 1 层拿到 JSON，再用该 JSON 的 `salt` 解第 2 层。

## 3. 算法细节

两层都使用相同的基本形式：

```
ciphertext = Base64( AES-128-CBC( plaintext_utf8, key_utf8, iv_utf8, PKCS5 ) )
```

- key/iv 直接取字符串的 UTF-8 字节（各 16 字节，即 AES-128）；
- 第 1 层的 iv 是 key 字符串的**字符反转**（如 `fudih4xp113znwp7` → `7pwnz311px4hiduf`）；
- 第 2 层的 key 是 `salt`，iv 是 `salt[::-1]`；
- 第 2 层在 `salt` 为空时视为“未加密”，原样返回（与官方实现一致）。

### 参考实现（Python）

```python
import base64
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

OUTER_KEY = b"fudih4xp113znwp7"
OUTER_IV = OUTER_KEY[::-1]

def aes_cbc_decrypt(ciphertext: bytes, key: bytes, iv: bytes) -> bytes:
    dec = Cipher(algorithms.AES(key), modes.CBC(iv)).decryptor()
    data = dec.update(ciphertext) + dec.finalize()
    pad = data[-1]
    if not 1 <= pad <= 16 or data[-pad:] != bytes([pad]) * pad:
        raise ValueError("padding 校验失败")
    return data[:-pad]

def decrypt_outer(field_b64: str) -> str:
    return aes_cbc_decrypt(base64.b64decode(field_b64), OUTER_KEY, OUTER_IV).decode()

def decrypt_inner(password_b64: str, salt: str) -> str:
    if not salt:
        return password_b64
    return aes_cbc_decrypt(base64.b64decode(password_b64), salt.encode(), salt[::-1].encode()).decode()
```

项目内的完整实现见 [`sqlark_decrypt/crypto.py`](../sqlark_decrypt/crypto.py)。

## 4. 逆向过程（方法记录）

1. **定位实现位置**：SQLark 是 Electron 前端 + Java 后端架构。连接文件由后端（jar）读取/写出，
   前端只负责发起“导出连接”请求。
2. **检索字符串常量**：在安装目录 `server/app/*.jar` 的 class 常量池中检索字段名
   `connectionDetail`、`superAttr`、`connectionInfo`，定位到连接信息相关类。
3. **定位加解密调用**：在 `BackUpUtil`（导出逻辑）中看到
   `AesUtil.encryptBase64(data, SALT, reverse(SALT))`，确认第 1 层；
   在 `ConnectionParamBaseVO` 的 `setPassword` / `decryptPassword` 中看到
   `AesUtil.decrypt(password, salt, reverse(salt))`，确认第 2 层。
4. **确认密钥来源**：`SysConnectionInfoConstant.SALT = "fudih4xp113znwp7"` 为硬编码常量；
   `salt` 由 `RandomUtil.randomString(16)` 在首次保存密码时生成。
5. **验证**：用已知明文做加密回环，密文与文件中的值逐字节一致；再反向解密得到原密码。
   如果结果与已知明文一致、且重加密能还原原文，即可确认算法与密钥。

> 具体类名：`com.dm.sqlark.system.util.BackUpUtil`、`com.dm.sqlark.system.util.SqlarkParseUtil`、
> `com.dm.sqlark.core.common.model.connect.ConnectionParamBaseVO`、
> `com.dm.sqlark.framework.util.AesUtil`、`com.dm.sqlark.system.constant.SysConnectionInfoConstant`。

## 5. 安全性评价

- **密钥硬编码在 jar 中**，且第 1 层 IV 由密钥反转得到；
- **CBC + 固定 IV/密钥是确定性加密**：相同密码产生相同密文，无法抵抗已知明文/对比分析；
- **第 2 层的密钥（salt）与密文存放在同一个 JSON**，等于“钥匙和锁放在一起”；
- 因此这只是**防肉眼窥视的混淆级保护，不是安全存储**。任何拿到连接文件的人都能还原明文密码。

对使用者的建议：不要把连接文件、导出的 CSV/JSON 放到共享目录/网盘/仓库；
生产环境凭据建议使用专门的密码管理器或短期凭证。

## 6. 兼容性与失败模式

- 在 SQLark 4.x 上验证通过；官方若更换密钥或算法，解析会失败（填充校验不通过）或得到乱码，
  本工具不会“猜”出错误密码；
- 若连接保存时未勾选“记住密码”，JSON 中没有 `password` 字段，此时密码为空；
- `superAttr` 解析失败不影响密码提取（它只是连接属性）。

## 7. 使用边界

本项目仅用于**本机**凭据找回与安全自查。请勿用于未授权的他人设备、未授权访问数据库或
任何违反当地法律法规的场景。

