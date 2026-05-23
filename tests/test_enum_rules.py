"""枚举规则生成器测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brute_force.enum_rules import (
    generate_digits,
    generate_lower_alpha,
    generate_upper_alpha,
    generate_mixed_alpha,
    generate_mixed,
    get_rule_generator,
    get_all_rule_ids,
    RULE_NAMES,
    RULE_DIGITS,
    RULE_LOWER_ALPHA,
    RULE_UPPER_ALPHA,
    RULE_MIXED_ALPHA,
    RULE_MIXED_DIGIT_LOWER,
    RULE_MIXED_DIGIT_UPPER,
    RULE_MIXED_ALL,
    DIGITS,
    LOWERCASE,
    UPPERCASE,
    ALPHANUM_LOWER,
    ALPHANUM_UPPER,
    ALPHANUM_ALL,
)


def test_digits():
    gen = generate_digits()
    first_10 = [next(gen) for _ in range(10)]
    assert first_10 == ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']


def test_lower_alpha():
    gen = generate_lower_alpha()
    first_5 = [next(gen) for _ in range(5)]
    assert first_5 == ['a', 'b', 'c', 'd', 'e']


def test_upper_alpha():
    gen = generate_upper_alpha()
    first_5 = [next(gen) for _ in range(5)]
    assert first_5 == ['A', 'B', 'C', 'D', 'E']


def test_mixed_alpha():
    gen = generate_mixed_alpha()
    first_5 = [next(gen) for _ in range(5)]
    # 至少包含1个小写和1个大写，所以从2位开始
    assert first_5 == ['aA', 'aB', 'aC', 'aD', 'aE']


def test_mixed_digit_lower():
    gen = generate_mixed(charset=ALPHANUM_LOWER, require_types=[DIGITS, LOWERCASE])
    first_5 = [next(gen) for _ in range(5)]
    # 至少包含1个数字和1个小写，所以从2位开始
    assert first_5 == ['0a', '0b', '0c', '0d', '0e']


def test_mixed_digit_upper():
    gen = generate_mixed(charset=ALPHANUM_UPPER, require_types=[DIGITS, UPPERCASE])
    first_5 = [next(gen) for _ in range(5)]
    # 至少包含1个数字和1个大写，所以从2位开始
    assert first_5 == ['0A', '0B', '0C', '0D', '0E']


def test_mixed_all():
    gen = generate_mixed(charset=ALPHANUM_ALL, require_types=[DIGITS, LOWERCASE, UPPERCASE])
    first_5 = [next(gen) for _ in range(5)]
    # 至少包含1数字+1小写+1大写，所以从3位开始
    assert first_5 == ['0aA', '0aB', '0aC', '0aD', '0aE']


def test_get_rule_generator():
    for rule_id in get_all_rule_ids():
        gen_func = get_rule_generator(rule_id)
        assert gen_func is not None, f"规则 {rule_id} 的生成器不存在"
        gen = gen_func()
        first = next(gen, None)
        assert first is not None, f"规则 {rule_id} 的生成器无输出"


def test_rule_names():
    assert RULE_NAMES[RULE_DIGITS] == "纯数字"
    assert RULE_NAMES[RULE_LOWER_ALPHA] == "纯小写字母"
    assert RULE_NAMES[RULE_UPPER_ALPHA] == "纯大写字母"
    assert RULE_NAMES[RULE_MIXED_ALPHA] == "大小写混合字母"
    assert RULE_NAMES[RULE_MIXED_DIGIT_LOWER] == "数字+小写混合"
    assert RULE_NAMES[RULE_MIXED_DIGIT_UPPER] == "数字+大写混合"
    assert RULE_NAMES[RULE_MIXED_ALL] == "数字+大小写混合"


def test_rules_no_overlap():
    """验证各规则生成的密码不重叠（抽样检查）"""
    # 规则1-3 纯字符，显然不重叠
    
    # 规则4 (大小写混合) 不含数字，与规则5-7 重叠检查
    gen4 = generate_mixed_alpha()
    samples4 = set(next(gen4) for _ in range(100))
    assert all(c not in DIGITS for s in samples4 for c in s), "规则4包含数字"
    
    # 规则5 (数字+小写) 不含大写
    gen5 = generate_mixed(charset=ALPHANUM_LOWER, require_types=[DIGITS, LOWERCASE])
    samples5 = set(next(gen5) for _ in range(100))
    assert all(c not in UPPERCASE for s in samples5 for c in s), "规则5包含大写"
    
    # 规则6 (数字+大写) 不含小写
    gen6 = generate_mixed(charset=ALPHANUM_UPPER, require_types=[DIGITS, UPPERCASE])
    samples6 = set(next(gen6) for _ in range(100))
    assert all(c not in LOWERCASE for s in samples6 for c in s), "规则6包含小写"
    
    # 规则7 (数字+大小写) 必须同时包含三种字符
    gen7 = generate_mixed(charset=ALPHANUM_ALL, require_types=[DIGITS, LOWERCASE, UPPERCASE])
    samples7 = set(next(gen7) for _ in range(100))
    for s in samples7:
        has_digit = any(c in DIGITS for c in s)
        has_lower = any(c in LOWERCASE for c in s)
        has_upper = any(c in UPPERCASE for c in s)
        assert has_digit and has_lower and has_upper, f"规则7密码 '{s}' 缺少某种字符类型"


if __name__ == "__main__":
    test_digits()
    test_lower_alpha()
    test_upper_alpha()
    test_mixed_alpha()
    test_mixed_digit_lower()
    test_mixed_digit_upper()
    test_mixed_all()
    test_get_rule_generator()
    test_rule_names()
    test_rules_no_overlap()
    print("enum_rules 测试全部通过")
