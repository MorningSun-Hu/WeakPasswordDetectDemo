"""工作进程/工作线程入口

每个 worker 按分配的规则生成密码候选，与目标密码比对。
使用批量更新减少锁/共享内存竞争。
增加异常捕获以便排查启动失败问题。
"""

import sys

from brute_force.enum_rules import (
    get_rule_generator,
    get_all_rule_ids,
)

BATCH_SIZE = 10000


def worker_process(worker_id: int, target: str, shared_state, rule_ids: list) -> None:
    """工作进程入口函数（用于 multiprocessing）"""
    try:
        _run_worker(worker_id, target, shared_state, rule_ids)
    except Exception as e:
        # 将错误信息输出到 stderr，方便调试
        print(f"[Worker {worker_id}] 异常退出: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)


def worker_thread(worker_id: int, target: str, shared_state, rule_ids: list) -> None:
    """工作线程入口函数（用于 threading 回退模式）"""
    _run_worker(worker_id, target, shared_state, rule_ids)


def _run_worker(worker_id: int, target: str, shared_state, rule_ids: list) -> None:
    """Worker 核心逻辑"""
    local_count = 0

    # 初始化当前规则状态
    if len(rule_ids) > 0:
        try:
            if hasattr(shared_state.current_rule[worker_id], "value"):
                shared_state.current_rule[worker_id].value = rule_ids[0]
            else:
                shared_state.current_rule[worker_id] = rule_ids[0]
        except IndexError:
            pass

    for rule_id in rule_ids:
        # 更新当前规则编号
        try:
            if hasattr(shared_state.current_rule[worker_id], "value"):
                shared_state.current_rule[worker_id].value = rule_id
            else:
                shared_state.current_rule[worker_id] = rule_id
        except Exception:
            pass

        if shared_state.is_terminated():
            break

        generator = get_rule_generator(rule_id)
        if generator is None:
            continue

        try:
            for candidate in generator():
                if shared_state.is_terminated():
                    break

                if candidate == target:
                    shared_state.set_found(candidate, worker_id)
                    local_count += 1
                    _flush_attempts(worker_id, local_count, shared_state)
                    return

                local_count += 1

                if local_count >= BATCH_SIZE:
                    _flush_attempts(worker_id, local_count, shared_state)
                    local_count = 0
        except StopIteration:
            pass

        if shared_state.is_terminated():
            break

    if local_count > 0:
        _flush_attempts(worker_id, local_count, shared_state)


def _flush_attempts(worker_id: int, count: int, shared_state) -> None:
    try:
        shared_state.add_attempts(worker_id, count)
    except Exception:
        pass


def assign_rules(worker_id: int, total_workers: int) -> list:
    """按轮询方式分配规则"""
    all_rules = get_all_rule_ids()
    assigned = []
    for i, rule_id in enumerate(all_rules):
        if i % total_workers == worker_id:
            assigned.append(rule_id)
    return assigned
