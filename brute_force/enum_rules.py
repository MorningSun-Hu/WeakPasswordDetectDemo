"""枚举规则生成器模块

按需求定义的顺序生成密码候选（7种规则，互不重叠）：
  1. 纯数字 (仅数字 0-9)
  2. 纯小写字母 (仅 a-z)
  3. 纯大写字母 (仅 A-Z)
  4. 大小写混合字母 (a-z + A-Z，至少各1个)
  5. 数字+小写全混合 (0-9 + a-z，至少各1个)
  6. 数字+大写全混合 (0-9 + A-Z，至少各1个)
  7. 数字+大小写全混合 (0-9 + a-z + A-Z，三种字符至少各1个)
"""

import itertools


# 预定义字符集
DIGITS = [str(i) for i in range(10)]
LOWERCASE = [chr(c) for c in range(ord("a"), ord("z") + 1)]
UPPERCASE = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
LETTERS = LOWERCASE + UPPERCASE
ALPHANUM_LOWER = DIGITS + LOWERCASE
ALPHANUM_UPPER = DIGITS + UPPERCASE
ALPHANUM_ALL = DIGITS + LOWERCASE + UPPERCASE

# 规则编号常量
RULE_DIGITS = 1
RULE_LOWER_ALPHA = 2
RULE_UPPER_ALPHA = 3
RULE_MIXED_ALPHA = 4
RULE_MIXED_DIGIT_LOWER = 5
RULE_MIXED_DIGIT_UPPER = 6
RULE_MIXED_ALL = 7

# 规则名称映射
RULE_NAMES = {
    RULE_DIGITS: "纯数字",
    RULE_LOWER_ALPHA: "纯小写字母",
    RULE_UPPER_ALPHA: "纯大写字母",
    RULE_MIXED_ALPHA: "大小写混合字母",
    RULE_MIXED_DIGIT_LOWER: "数字+小写混合",
    RULE_MIXED_DIGIT_UPPER: "数字+大写混合",
    RULE_MIXED_ALL: "数字+大小写混合",
}


def generate_digits(min_len: int = 1, max_len: int = 8):
    """生成 1位到8位纯数字

    顺序: 0, 1, ..., 9, 00, 01, ..., 99, 000, ...
    """
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(DIGITS, repeat=length):
            yield "".join(combo)


def generate_lower_alpha(min_len: int = 1, max_len: int = 8):
    """生成 1位到8位纯小写字母

    顺序: a, b, ..., z, aa, ab, ..., zz, aaa, ...
    """
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(LOWERCASE, repeat=length):
            yield "".join(combo)


def generate_upper_alpha(min_len: int = 1, max_len: int = 8):
    """生成 1位到8位纯大写字母

    顺序: A, B, ..., Z, AA, AB, ..., ZZ, AAA, ...
    """
    for length in range(min_len, max_len + 1):
        for combo in itertools.product(UPPERCASE, repeat=length):
            yield "".join(combo)


def generate_mixed_alpha(min_len: int = 1, max_len: int = 8):
    """生成 1位到8位大小写混合字母

    约束：至少包含1个小写和1个大写
    排除：纯小写、纯大写
    """
    for length in range(min_len, max_len + 1):
        if length < 2:
            continue  # 至少2位才可能同时包含大小写
        for combo in itertools.product(LETTERS, repeat=length):
            has_lower = any(c in LOWERCASE for c in combo)
            has_upper = any(c in UPPERCASE for c in combo)
            if has_lower and has_upper:
                yield "".join(combo)


def generate_mixed(min_len: int = 1, max_len: int = 8, charset=None, require_types=None):
    """生成指定字符集的混合密码

    charset: 字符集列表
    require_types: 列表，指定必须出现的字符子集类别
                   例如: [DIGITS, LOWERCASE] 表示必须至少包含1个数字和1个小写
    """
    if charset is None:
        charset = ALPHANUM_LOWER
    
    for length in range(min_len, max_len + 1):
        if require_types and length < len(require_types):
            continue  # 长度不足以保证每种类型至少出现一次
        
        for combo in itertools.product(charset, repeat=length):
            if require_types:
                # 检查是否每种类型都至少出现一次
                if not all(any(c in req_set for c in combo) for req_set in require_types):
                    continue
            yield "".join(combo)


def get_rule_generator(rule_id: int):
    """根据规则编号返回对应的生成器函数

    Returns:
        生成器函数，调用后返回迭代器
    """
    generators = {
        RULE_DIGITS: lambda: generate_digits(),
        RULE_LOWER_ALPHA: lambda: generate_lower_alpha(),
        RULE_UPPER_ALPHA: lambda: generate_upper_alpha(),
        RULE_MIXED_ALPHA: lambda: generate_mixed_alpha(),
        RULE_MIXED_DIGIT_LOWER: lambda: generate_mixed(
            charset=ALPHANUM_LOWER, require_types=[DIGITS, LOWERCASE]
        ),
        RULE_MIXED_DIGIT_UPPER: lambda: generate_mixed(
            charset=ALPHANUM_UPPER, require_types=[DIGITS, UPPERCASE]
        ),
        RULE_MIXED_ALL: lambda: generate_mixed(
            charset=ALPHANUM_ALL, require_types=[DIGITS, LOWERCASE, UPPERCASE]
        ),
    }
    return generators.get(rule_id)


def get_all_rule_ids():
    """返回所有规则编号列表（按执行顺序）"""
    return [
        RULE_DIGITS,
        RULE_LOWER_ALPHA,
        RULE_UPPER_ALPHA,
        RULE_MIXED_ALPHA,
        RULE_MIXED_DIGIT_LOWER,
        RULE_MIXED_DIGIT_UPPER,
        RULE_MIXED_ALL,
    ]
