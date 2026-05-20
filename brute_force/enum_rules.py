"""枚举规则生成器模块

按需求定义的顺序生成密码候选：
  a. 1位到8位纯数字
  b. 1位英文字母（先小写后大写）开头 + 1位到8位数字
  c. 1位到8位数字 + 1位字母结尾
  d. 1位到8位数字+小写英文字母混合
  e. 1位到8位数字+大小写英文字母混合
"""

import itertools


# 预定义字符集
DIGITS = [str(i) for i in range(10)]
LOWERCASE = [chr(c) for c in range(ord("a"), ord("z") + 1)]
UPPERCASE = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
LETTERS = LOWERCASE + UPPERCASE
ALPHANUM_LOWER = DIGITS + LOWERCASE
ALPHANUM_ALL = DIGITS + LOWERCASE + UPPERCASE

# 规则编号常量
RULE_DIGITS = 1
RULE_LETTER_PREFIX_DIGIT = 2
RULE_DIGIT_LETTER_SUFFIX = 3
RULE_MIXED_LOWER = 4
RULE_MIXED_ALL = 5

# 规则名称映射
RULE_NAMES = {
    RULE_DIGITS: "纯数字",
    RULE_LETTER_PREFIX_DIGIT: "字母开头+数字",
    RULE_DIGIT_LETTER_SUFFIX: "数字+字母结尾",
    RULE_MIXED_LOWER: "数字+小写混合",
    RULE_MIXED_ALL: "数字+大小写混合",
}


def generate_digits(min_len: int = 1, max_len: int = 8):
    """生成 1位到8位纯数字

    顺序: 0, 1, ..., 9, 00, 01, ..., 99, 000, ...
    """
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(DIGITS, repeat=length):
            yield "".join(combo)


def generate_letter_prefix_digit(min_dlen: int = 1, max_dlen: int = 8):
    """生成字母开头+数字

    字母顺序：先小写后大写 (a-z, A-Z)
    数字部分：1位到8位
    例如: a0, a1, ..., a9, aa0, ... z99999999, A0, ..., Z99999999
    """
    for letter in LETTERS:
        for dlen in range(min_dlen, max_dlen + 1):
            for combo in itertools.product(DIGITS, repeat=dlen):
                yield letter + "".join(combo)


def generate_digit_letter_suffix(min_dlen: int = 1, max_dlen: int = 8):
    """生成数字+字母结尾

    数字部分：1位到8位
    字母顺序：先小写后大写
    例如: 0a, 1a, ..., 9z, 00a, ..., 99999999z
    """
    for dlen in range(min_dlen, max_dlen + 1):
        for combo in itertools.product(DIGITS, repeat=dlen):
            digit_part = "".join(combo)
            for letter in LETTERS:
                yield digit_part + letter


def generate_mixed(min_len: int = 1, max_len: int = 8, charset=None):
    """生成指定字符集的混合密码

    charset: 字符集列表，默认使用数字+小写字母
    """
    if charset is None:
        charset = ALPHANUM_LOWER
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(charset, repeat=length):
            yield "".join(combo)


def get_rule_generator(rule_id: int):
    """根据规则编号返回对应的生成器函数

    Returns:
        生成器函数，调用后返回迭代器
    """
    generators = {
        RULE_DIGITS: lambda: generate_digits(),
        RULE_LETTER_PREFIX_DIGIT: lambda: generate_letter_prefix_digit(),
        RULE_DIGIT_LETTER_SUFFIX: lambda: generate_digit_letter_suffix(),
        RULE_MIXED_LOWER: lambda: generate_mixed(charset=ALPHANUM_LOWER),
        RULE_MIXED_ALL: lambda: generate_mixed(charset=ALPHANUM_ALL),
    }
    return generators.get(rule_id)


def get_all_rule_ids():
    """返回所有规则编号列表（按执行顺序）"""
    return [
        RULE_DIGITS,
        RULE_LETTER_PREFIX_DIGIT,
        RULE_DIGIT_LETTER_SUFFIX,
        RULE_MIXED_LOWER,
        RULE_MIXED_ALL,
    ]
