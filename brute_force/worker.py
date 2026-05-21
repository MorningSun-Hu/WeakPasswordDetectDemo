"""工作进程/工作线程入口

每个 worker 按分配的规则生成密码候选，与目标密码比对。
增加了详细的异常捕获和调试日志输出，便于排查 Windows spawn 模式下的崩溃问题。
"""

import sys
import os

from brute_force.enum_rules import (
    get_rule_generator,
    get_all_rule_ids,
)

BATCH_SIZE = 10000


def worker_process(worker_id: int, target: str, shared_state, rule_ids: list) -> None:
    """工作进程入口函数（用于 multiprocessing）"""
    # 在 Windows spawn 模式下，子进程的 stdout 可能被重定向，写入文件更保险
    log_file = "worker_%d.log" % worker_id
    try:
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("Worker %d started. Target len: %d, Rules: %s\n" % (worker_id, len(target), rule_ids))
            f.flush()
            _run_worker(worker_id, target, shared_state, rule_ids, f)
    except Exception as e:
        # 记录异常到文件
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                import traceback
                f.write("Worker %d CRASHED: %s\n" % (worker_id, str(e)))
                traceback.print_exc(file=f)
        except:
            pass


def worker_thread(worker_id: int, target: str, shared_state, rule_ids: list) -> None:
    """工作线程入口函数（用于 threading 回退模式）"""
    _run_worker(worker_id, target, shared_state, rule_ids, sys.stdout)


def _run_worker(worker_id: int, target: str, shared_state, rule_ids: list, log) -> None:
    """Worker 核心逻辑"""
    local_count = 0

    log.write("Worker %d: Entering loop.\n" % worker_id)
    log.flush()

    # 遍历分配到的规则
    for idx, rule_id in enumerate(rule_ids):
        log.write("Worker %d: Starting rule %d\n" % (worker_id, rule_id))
        log.flush()

        # 更新当前规则编号
        try:
            if hasattr(shared_state.current_rule[worker_id], "value"):
                shared_state.current_rule[worker_id].value = rule_id
            else:
                shared_state.current_rule[worker_id] = rule_id
        except Exception as e:
            log.write("Worker %d: Error updating rule: %s\n" % (worker_id, e))
            log.flush()

        # 检查是否已终止
        if shared_state.is_terminated():
            log.write("Worker %d: Terminated before rule %d\n" % (worker_id, rule_id))
            log.flush()
            break

        generator = get_rule_generator(rule_id)
        if generator is None:
            log.write("Worker %d: Generator for rule %d is None\n" % (worker_id, rule_id))
            log.flush()
            continue

        try:
            # 开始枚举
            count_in_rule = 0
            for candidate in generator():
                if shared_state.is_terminated():
                    break

                if candidate == target:
                    log.write("Worker %d: FOUND PASSWORD!\n" % worker_id)
                    log.flush()
                    shared_state.set_found(candidate, worker_id)
                    local_count += 1
                    _flush_attempts(worker_id, local_count, shared_state, log)
                    return

                local_count += 1
                count_in_rule += 1

                # 每 10 万次写一次日志
                if count_in_rule % 100000 == 0:
                    log.write("Worker %d: Rule %d progress: %d candidates\n" % (worker_id, rule_id, count_in_rule))
                    log.flush()

                if local_count >= BATCH_SIZE:
                    _flush_attempts(worker_id, local_count, shared_state, log)
                    local_count = 0
        except StopIteration:
            pass

        if shared_state.is_terminated():
            break

    # 刷新剩余计数
    if local_count > 0:
        _flush_attempts(worker_id, local_count, shared_state, log)

    log.write("Worker %d: Finished all rules.\n" % worker_id)
    log.flush()


def _flush_attempts(worker_id: int, count: int, shared_state, log) -> None:
    try:
        shared_state.add_attempts(worker_id, count)
    except Exception as e:
        log.write("Worker %d: Error flushing attempts: %s\n" % (worker_id, e))
        log.flush()


def assign_rules(worker_id: int, total_workers: int) -> list:
    """按轮询方式分配规则"""
    all_rules = get_all_rule_ids()
    assigned = []
    for i, rule_id in enumerate(all_rules):
        if i % total_workers == worker_id:
            assigned.append(rule_id)
    return assigned
