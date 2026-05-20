"""枚举规则生成器测试"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brute_force.enum_rules import (
    generate_digits,
    generate_letter_prefix_digit,
    generate_digit_letter_suffix,
    generate_mixed,
    get_rule_generator,
    get_all_rule_ids,
    RULE_NAMES,
    RULE_DIGITS,
    RULE_LETTER_PREFIX_DIGIT,
    RULE_DIGIT_LETTER_SUFFIX,
    RULE_MIXED_LOWER,
    RULE_MIXED_ALL,
)


def test_digits():
    gen = generate_digits()
    first_10 = [next(gen) for _ in range(10)]
    assert first_10 == ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']


def test_letter_prefix_digit():
    gen = generate_letter_prefix_digit()
    first = next(gen)
    assert first == 'a0'


def test_digit_letter_suffix():
    gen = generate_digit_letter_suffix()
    first = next(gen)
    assert first == '0a'


def test_mixed_default():
    gen = generate_mixed()
    first_10 = [next(gen) for _ in range(10)]
    # 默认字符集为 数字+小写
    assert first_10 == ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']


def test_get_rule_generator():
    for rule_id in get_all_rule_ids():
        gen_func = get_rule_generator(rule_id)
        assert gen_func is not None
        gen = gen_func()
        assert next(gen) is not None


def test_rule_names():
    assert RULE_NAMES[RULE_DIGITS] == "纯数字"
    assert RULE_NAMES[RULE_LETTER_PREFIX_DIGIT] == "字母开头+数字"
    assert RULE_NAMES[RULE_DIGIT_LETTER_SUFFIX] == "数字+字母结尾"
    assert RULE_NAMES[RULE_MIXED_LOWER] == "数字+小写混合"
    assert RULE_NAMES[RULE_MIXED_ALL] == "数字+大小写混合"


if __name__ == "__main__":
    test_digits()
    test_letter_prefix_digit()
    test_digit_letter_suffix()
    test_mixed_default()
    test_get_rule_generator()
    test_rule_names()
    print("enum_rules 测试全部通过")
