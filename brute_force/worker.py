"""工作进程/工作线程入口"""

import sys
import os
import time

# 立即尝试写入启动日志，验证进程是否真的启动了
_log_file = "worker_%d.log" % os.getpid()
try:
    with open(_log_file, "w", encoding="utf-8") as _f:
        _f.write("Worker PID %d starting...\n" % os.getpid())
        _f.write("CWD: %s\n" % os.getcwd())
        _f.flush()
except:
    pass

def _log(msg):
    try:
        with open(_log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
            f.flush()
    except:
        pass

_log("Imports starting...")

try:
    from brute_force.enum_rules import (
        get_rule_generator,
        get_all_rule_ids,
    )
    _log("Imports successful.")
except Exception as e:
    _log("Import failed: %s" % e)
    import traceback
    _log(traceback.format_exc())
    raise

BATCH_SIZE = 10000

def worker_process(worker_id: int, target: str, shared_state, rule_ids: list) -> None:
    """工作进程入口函数"""
    _log("worker_process called with ID: %d, Rules: %s" % (worker_id, rule_ids))
    try:
        _run_worker(worker_id, target, shared_state, rule_ids)
    except Exception as e:
        _log("CRASHED: %s" % e)
        import traceback
        _log(traceback.format_exc())

def worker_thread(worker_id: int, target: str, shared_state, rule_ids: list) -> None:
    _log("worker_thread called with ID: %d" % worker_id)
    _run_worker(worker_id, target, shared_state, rule_ids, sys.stdout)

def _run_worker(worker_id: int, target: str, shared_state, rule_ids: list, log=None) -> None:
    """Worker 核心逻辑"""
    _log("_run_worker started.")
    local_count = 0

    for idx, rule_id in enumerate(rule_ids):
        _log("Processing rule %d" % rule_id)
        
        try:
            if hasattr(shared_state.current_rule[worker_id], "value"):
                shared_state.current_rule[worker_id].value = rule_id
            else:
                shared_state.current_rule[worker_id] = rule_id
        except Exception as e:
            _log("Error updating rule: %s" % e)

        if shared_state.is_terminated():
            _log("Terminated before rule %d" % rule_id)
            break

        generator = get_rule_generator(rule_id)
        if generator is None:
            _log("Generator for rule %d is None" % rule_id)
            continue

        _log("Starting generator for rule %d" % rule_id)
        try:
            for candidate in generator():
                if shared_state.is_terminated():
                    break

                # 检查是否暂停
                while shared_state.is_paused():
                    if shared_state.is_terminated():
                        break
                    time.sleep(0.05)

                if candidate == target:
                    _log("FOUND PASSWORD: %s" % candidate)
                    shared_state.set_found(candidate, worker_id)
                    local_count += 1
                    _flush_attempts(worker_id, local_count, shared_state)
                    return

                local_count += 1

                if local_count >= BATCH_SIZE:
                    _flush_attempts(worker_id, local_count, shared_state)
                    local_count = 0
        except Exception as e:
            _log("Generator error: %s" % e)
            import traceback
            _log(traceback.format_exc())

        if shared_state.is_terminated():
            break

    if local_count > 0:
        _flush_attempts(worker_id, local_count, shared_state)

    _log("Worker %d finished all tasks." % worker_id)

def _flush_attempts(worker_id: int, count: int, shared_state, log=None) -> None:
    try:
        shared_state.add_attempts(worker_id, count)
        _log("Flushed %d attempts for worker %d" % (count, worker_id))
    except Exception as e:
        _log("Flush error: %s" % e)

def assign_rules(worker_id: int, total_workers: int) -> list:
    all_rules = get_all_rule_ids()
    assigned = []
    for i, rule_id in enumerate(all_rules):
        if i % total_workers == worker_id:
            assigned.append(rule_id)
    return assigned
