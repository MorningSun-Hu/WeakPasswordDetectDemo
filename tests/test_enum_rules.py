"""枚举规则生成器测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brute_force.enum_rules import (
    count_weak_dict,
    load_weak_dict,
    generate_digits,
    generate_lower_alpha,
    generate_upper_alpha,
    generate_mixed_alpha,
    generate_mixed,
    get_rule_generator,
    get_all_rule_ids,
    RULE_NAMES,
    RULE_WEAK_DICT,
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


def test_weak_dict_count():
    count = count_weak_dict()
    assert count > 0, "弱口令库应为非空"


def test_weak_dict_range():
    gen = load_weak_dict(0, 5)
    first_5 = list(gen)
    assert len(first_5) == 5
    assert first_5[0] == '123456'


def test_digits_length():
    gen = generate_digits(2)
    items = list(gen)
    assert items[0] == '00'
    assert items[-1] == '99'
    assert len(items) == 100


def test_lower_alpha_length():
    gen = generate_lower_alpha(2)
    items = list(gen)
    assert items[0] == 'aa'
    assert items[-1] == 'zz'
    assert len(items) == 26 * 26


def test_upper_alpha_length():
    gen = generate_upper_alpha(2)
    items = list(gen)
    assert items[0] == 'AA'
    assert items[-1] == 'ZZ'


def test_mixed_alpha_length():
    gen = generate_mixed_alpha(2)
    items = list(gen)
    assert items[0] == 'aA'
    # 应该包含至少一个小写和一个大写
    for item in items[:10]:
        has_lower = any(c in LOWERCASE for c in item)
        has_upper = any(c in UPPERCASE for c in item)
        assert has_lower and has_upper, f"'{item}' 不满足混合条件"


def test_mixed_digit_lower_length():
    gen = generate_mixed(2, charset=ALPHANUM_LOWER, require_types=[DIGITS, LOWERCASE])
    items = list(gen)
    assert items[0] == '0a'
    # 验证至少包含一个数字和一个小写
    for item in items[:10]:
        has_digit = any(c in DIGITS for c in item)
        has_lower = any(c in LOWERCASE for c in item)
        assert has_digit and has_lower, f"'{item}' 不满足条件"


def test_mixed_digit_upper_length():
    gen = generate_mixed(2, charset=ALPHANUM_UPPER, require_types=[DIGITS, UPPERCASE])
    items = list(gen)
    assert items[0] == '0A'


def test_mixed_all_length():
    gen = generate_mixed(3, charset=ALPHANUM_ALL, require_types=[DIGITS, LOWERCASE, UPPERCASE])
    items = list(gen)
    assert items[0] == '0aA'
    for item in items[:10]:
        has_digit = any(c in DIGITS for c in item)
        has_lower = any(c in LOWERCASE for c in item)
        has_upper = any(c in UPPERCASE for c in item)
        assert has_digit and has_lower and has_upper, f"'{item}' 缺少某种字符类型"


def test_get_rule_generator():
    for rule_id in get_all_rule_ids():
        if rule_id == RULE_WEAK_DICT:
            gen_func = get_rule_generator(rule_id)
        elif rule_id == RULE_MIXED_ALL:
            # 规则7需要至少3个字符
            gen_func = get_rule_generator(rule_id, length=3)
        else:
            gen_func = get_rule_generator(rule_id, length=2)
        assert gen_func is not None, f"规则 {rule_id} 的生成器不存在"
        gen = gen_func()
        first = next(gen, None)
        assert first is not None, f"规则 {rule_id} 的生成器无输出"


def test_rule_names():
    assert RULE_NAMES[RULE_WEAK_DICT] == "弱口令库"
    assert RULE_NAMES[RULE_DIGITS] == "纯数字"
    assert RULE_NAMES[RULE_LOWER_ALPHA] == "纯小写字母"
    assert RULE_NAMES[RULE_UPPER_ALPHA] == "纯大写字母"
    assert RULE_NAMES[RULE_MIXED_ALPHA] == "大小写混合字母"
    assert RULE_NAMES[RULE_MIXED_DIGIT_LOWER] == "数字+小写混合"
    assert RULE_NAMES[RULE_MIXED_DIGIT_UPPER] == "数字+大写混合"
    assert RULE_NAMES[RULE_MIXED_ALL] == "数字+大小写混合"


if __name__ == "__main__":
    test_weak_dict_count()
    test_weak_dict_range()
    test_digits_length()
    test_lower_alpha_length()
    test_upper_alpha_length()
    test_mixed_alpha_length()
    test_mixed_digit_lower_length()
    test_mixed_digit_upper_length()
    test_mixed_all_length()
    test_get_rule_generator()
    test_rule_names()
    print("enum_rules 测试全部通过")
