"""工具函数模块

提供密码校验等通用工具函数。
"""

import string

# 允许的字符集：字母 + 数字
_ALLOWED_CHARS = set(string.ascii_letters + string.digits)


def validate_password(password: str) -> tuple[bool, list[str]]:
    """校验密码格式

    仅允许 ASCII 字母 (a-z, A-Z) 和数字 (0-9)。
    与 CLI 界面的校验逻辑保持一致。

    Args:
        password: 待校验的密码字符串

    Returns:
        tuple[bool, list[str]]: (是否合法, 非法字符列表)
    """
    invalid_chars = list(set(c for c in password if c not in _ALLOWED_CHARS))
    return len(invalid_chars) == 0, invalid_chars
