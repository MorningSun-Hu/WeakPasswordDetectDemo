"""枚举规则生成器模块

8种规则（含弱口令库），按执行顺序：
  0. 弱口令库查询（Top 10000常见密码）
  1. 纯数字 (仅数字 0-9)
  2. 纯小写字母 (仅 a-z)
  3. 纯大写字母 (仅 A-Z)
  4. 大小写混合字母 (a-z + A-Z，至少各1个)
  5. 数字+小写全混合 (0-9 + a-z，至少各1个)
  6. 数字+大写全混合 (0-9 + A-Z，至少各1个)
  7. 数字+大小写全混合 (0-9 + a-z + A-Z，三种字符至少各1个)
"""

import itertools
from pathlib import Path


# 预定义字符集
DIGITS = [str(i) for i in range(10)]
LOWERCASE = [chr(c) for c in range(ord("a"), ord("z") + 1)]
UPPERCASE = [chr(c) for c in range(ord("A"), ord("Z") + 1)]
LETTERS = LOWERCASE + UPPERCASE
ALPHANUM_LOWER = DIGITS + LOWERCASE
ALPHANUM_UPPER = DIGITS + UPPERCASE
ALPHANUM_ALL = DIGITS + LOWERCASE + UPPERCASE

# 规则编号常量
RULE_WEAK_DICT = 0
RULE_DIGITS = 1
RULE_LOWER_ALPHA = 2
RULE_UPPER_ALPHA = 3
RULE_MIXED_ALPHA = 4
RULE_MIXED_DIGIT_LOWER = 5
RULE_MIXED_DIGIT_UPPER = 6
RULE_MIXED_ALL = 7

# 规则名称映射
RULE_NAMES = {
    RULE_WEAK_DICT: "弱口令库",
    RULE_DIGITS: "纯数字",
    RULE_LOWER_ALPHA: "纯小写字母",
    RULE_UPPER_ALPHA: "纯大写字母",
    RULE_MIXED_ALPHA: "大小写混合字母",
    RULE_MIXED_DIGIT_LOWER: "数字+小写混合",
    RULE_MIXED_DIGIT_UPPER: "数字+大写混合",
    RULE_MIXED_ALL: "数字+大小写混合",
}

# 弱口令库文件路径
_WEAK_DICT_PATH = Path(__file__).parent / "data" / "weak_passwords.txt"


def count_weak_dict():
    """统计弱口令库行数"""
    try:
        with open(_WEAK_DICT_PATH, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except FileNotFoundError:
        return 0


def load_weak_dict(start_line: int = 0, end_line: int = None):
    """加载弱口令库的指定行范围

    Args:
        start_line: 起始行索引（0-based）
        end_line: 结束行索引（不包含），None表示到末尾
    """
    try:
        with open(_WEAK_DICT_PATH, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i < start_line:
                    continue
                if end_line is not None and i >= end_line:
                    break
                pwd = line.strip()
                if pwd:
                    yield pwd
    except FileNotFoundError:
        pass


def generate_digits(length: int):
    """生成指定长度的纯数字"""
    for combo in itertools.product(DIGITS, repeat=length):
        yield "".join(combo)


def generate_lower_alpha(length: int):
    """生成指定长度的纯小写字母"""
    for combo in itertools.product(LOWERCASE, repeat=length):
        yield "".join(combo)


def generate_upper_alpha(length: int):
    """生成指定长度的纯大写字母"""
    for combo in itertools.product(UPPERCASE, repeat=length):
        yield "".join(combo)


def generate_mixed_alpha(length: int):
    """生成指定长度的大小写混合字母

    约束：至少包含1个小写和1个大写
    """
    if length < 2:
        return
    for combo in itertools.product(LETTERS, repeat=length):
        has_lower = any(c in LOWERCASE for c in combo)
        has_upper = any(c in UPPERCASE for c in combo)
        if has_lower and has_upper:
            yield "".join(combo)


def generate_mixed(length: int, charset=None, require_types=None):
    """生成指定长度的混合密码

    charset: 字符集列表
    require_types: 列表，指定必须出现的字符子集类别
    """
    if charset is None:
        charset = ALPHANUM_LOWER
    
    if require_types and length < len(require_types):
        return
    
    for combo in itertools.product(charset, repeat=length):
        if require_types:
            if not all(any(c in req_set for c in combo) for req_set in require_types):
                continue
        yield "".join(combo)


def get_rule_generator(rule_id: int, length: int = None):
    """根据规则编号返回对应的生成器函数

    Args:
        rule_id: 规则编号
        length: 密码长度（枚举规则需要，弱口令库忽略）
    
    Returns:
        生成器函数，调用后返回迭代器
    """
    if rule_id == RULE_WEAK_DICT:
        return lambda: load_weak_dict()
    
    if length is None:
        return None
    
    generators = {
        RULE_DIGITS: lambda: generate_digits(length),
        RULE_LOWER_ALPHA: lambda: generate_lower_alpha(length),
        RULE_UPPER_ALPHA: lambda: generate_upper_alpha(length),
        RULE_MIXED_ALPHA: lambda: generate_mixed_alpha(length),
        RULE_MIXED_DIGIT_LOWER: lambda: generate_mixed(
            length=length, charset=ALPHANUM_LOWER, require_types=[DIGITS, LOWERCASE]
        ),
        RULE_MIXED_DIGIT_UPPER: lambda: generate_mixed(
            length=length, charset=ALPHANUM_UPPER, require_types=[DIGITS, UPPERCASE]
        ),
        RULE_MIXED_ALL: lambda: generate_mixed(
            length=length, charset=ALPHANUM_ALL, require_types=[DIGITS, LOWERCASE, UPPERCASE]
        ),
    }
    return generators.get(rule_id)


def get_all_rule_ids():
    """返回所有规则编号列表（按执行顺序）"""
    return [
        RULE_WEAK_DICT,
        RULE_DIGITS,
        RULE_LOWER_ALPHA,
        RULE_UPPER_ALPHA,
        RULE_MIXED_ALPHA,
        RULE_MIXED_DIGIT_LOWER,
        RULE_MIXED_DIGIT_UPPER,
        RULE_MIXED_ALL,
    ]
