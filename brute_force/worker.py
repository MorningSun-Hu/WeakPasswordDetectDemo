"""工作线程模块

每个工作线程按分配的枚举规则生成密码候选，与目标密码比对。
使用批量更新减少锁竞争。
"""

import threading
import time

from brute_force.enum_rules import (
    get_rule_generator,
    get_all_rule_ids,
    RULE_NAMES,
)


# 批量更新阈值：每尝试 BATCH_SIZE 次后更新一次共享计数
BATCH_SIZE = 10000


def worker_thread(
    worker_id: int,
    target: str,
    shared_state,
    rule_ids: list,
) -> None:
    """工作线程入口函数

    Args:
        worker_id: 线程编号 (0-based)
        target: 目标密码
        shared_state: SharedState 实例
        rule_ids: 分配给该线程的规则编号列表
    """
    local_count = 0
    total_found = False

    for rule_id in rule_ids:
        # 更新当前规则编号
        with shared_state._lock:
            shared_state.current_rule[worker_id] = rule_id

        # 检查是否已被终止
        if shared_state.is_terminated():
            break

        generator = get_rule_generator(rule_id)
        if generator is None:
            continue

        for candidate in generator():
            # 检查终止信号
            if shared_state.is_terminated():
                break

            # 密码比对
            if candidate == target:
                shared_state.set_found(candidate, worker_id)
                local_count += 1
                _flush_attempts(worker_id, local_count, shared_state)
                return

            # 本地计数累加
            local_count += 1

            # 批量刷新到共享状态
            if local_count >= BATCH_SIZE:
                _flush_attempts(worker_id, local_count, shared_state)
                local_count = 0

        # 当前规则已完成，检查是否终止
        if shared_state.is_terminated():
            break

    # 所有规则完成，刷新剩余计数
    if local_count > 0:
        _flush_attempts(worker_id, local_count, shared_state)


def _flush_attempts(worker_id: int, count: int, shared_state) -> None:
    """将本地累计尝试次数刷新到共享状态"""
    shared_state.add_attempts(worker_id, count)


def assign_rules(worker_id: int, total_workers: int) -> list:
    """为指定工作线程分配规则

    策略：按轮询方式分配规则，确保负载相对均衡。
    Worker 0: 规则 1, 4
    Worker 1: 规则 2, 5
    Worker 2: 规则 3

    Args:
        worker_id: 线程编号 (0-based)
        total_workers: 总线程数

    Returns:
        分配给该线程的规则编号列表
    """
    all_rules = get_all_rule_ids()
    assigned = []
    for i, rule_id in enumerate(all_rules):
        if i % total_workers == worker_id:
            assigned.append(rule_id)
    return assigned
