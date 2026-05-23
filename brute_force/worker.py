"""工作进程/工作线程入口

动态任务队列模式：所有worker同时处理同一规则，按长度/行数分段领取任务。
"""

import sys
import os
import time
import signal
import threading

# 立即尝试写入启动日志
_log_file = "worker_%d.log" % os.getpid()
_thread_local = threading.local()
try:
    with open(_log_file, "w", encoding="utf-8") as _f:
        _f.write("Worker PID %d starting...\n" % os.getpid())
        _f.write("CWD: %s\n" % os.getcwd())
        _f.flush()
except:
    pass

def _log(msg):
    try:
        log_file = getattr(_thread_local, "log_file", _log_file)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
            f.flush()
    except:
        pass

_log("Imports starting...")

try:
    from brute_force.enum_rules import (
        get_rule_generator,
        load_weak_dict,
        get_all_rule_ids,
        RULE_WEAK_DICT,
    )
    _log("Imports successful.")
except Exception as e:
    _log("Import failed: %s" % e)
    import traceback
    _log(traceback.format_exc())
    raise

BATCH_SIZE = 10000

def worker_process(worker_id: int, target: str, shared_state, worker_count: int, max_len: int = 8) -> None:
    """工作进程入口函数"""
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    _thread_local.log_file = "worker_%d_%d.log" % (os.getpid(), worker_id)
    
    _log("worker_process called with ID: %d" % worker_id)
    try:
        _run_worker(worker_id, target, shared_state, worker_count, max_len)
    except KeyboardInterrupt:
        _log("Worker %d received KeyboardInterrupt, exiting gracefully." % worker_id)
    except Exception as e:
        _log("CRASHED: %s" % e)
        import traceback
        _log(traceback.format_exc())

def worker_thread(worker_id: int, target: str, shared_state, worker_count: int, max_len: int = 8) -> None:
    _thread_local.log_file = "worker_thread_%d.log" % worker_id
    _log("worker_thread called with ID: %d" % worker_id)
    _run_worker(worker_id, target, shared_state, worker_count, max_len, sys.stdout)

def _run_worker(worker_id: int, target: str, shared_state, worker_count: int, max_len: int = 8, log=None) -> None:
    """Worker 核心逻辑 - 动态任务队列模式"""
    _log("_run_worker started.")
    
    empty_count = 0
    max_empty_retries = 20  # 最多重试20次（约2秒），仅针对真正的无任务状态
    
    while True:
        # 领取下一个任务块
        # 返回值: (rule_id, start, end)
        # rule_id=0, start=-1, end=-1: 等待中（字典处理中或规则切换中）
        # rule_id=None: 无任务（所有规则已完成）
        # rule_id=0: start/end 是行索引
        # rule_id>0: start/end 是长度值（相同，因为每次分配一个长度）
        rule_id, start, end = shared_state.get_next_task(worker_count, max_len)
        
        if rule_id is None:
            if start == -1 and end == -1:
                _log("Worker %d: termination requested, exiting." % worker_id)
                break
            # 真正的无任务（所有规则已完成）
            empty_count += 1
            _log("Worker %d: no task, retry %d/%d" % (worker_id, empty_count, max_empty_retries))
            if empty_count >= max_empty_retries:
                _log("Worker %d: no more tasks after %d retries, exiting." % (worker_id, max_empty_retries))
                break
            time.sleep(0.1)
            continue
        
        if rule_id == 0 and start == -1 and end == -1:
            # 等待中（字典处理中或规则切换中），重置重试计数器
            _log("Worker %d: waiting for task..." % worker_id)
            empty_count = 0
            time.sleep(0.1)
            continue
        
        empty_count = 0  # 重置重试计数器
        
        if rule_id == RULE_WEAK_DICT:
            _log("Worker %d: processing weak dict, lines [%d, %d)" % (worker_id, start, end))
            _process_weak_dict(worker_id, target, shared_state, start, end)
        else:
            length = start  # start == end for enum rules
            _log("Worker %d: processing rule %d, length %d" % (worker_id, rule_id, length))
            _process_enum_rule(worker_id, target, shared_state, rule_id, length)

def _process_weak_dict(worker_id: int, target: str, shared_state, start_line: int, end_line: int) -> None:
    """处理弱口令库任务块"""
    local_count = 0
    
    try:
        for candidate in load_weak_dict(start_line, end_line):
            if shared_state.is_terminated():
                break

            while shared_state.is_paused():
                if shared_state.is_terminated():
                    break
                time.sleep(0.05)

            if candidate == target:
                _log("FOUND PASSWORD: %s" % candidate)
                shared_state.set_found(candidate, worker_id)
                local_count += 1
                _flush_attempts(worker_id, local_count, shared_state)
                _decrement_dict_active(shared_state)
                return

            local_count += 1

            if local_count >= BATCH_SIZE:
                _flush_attempts(worker_id, local_count, shared_state)
                local_count = 0
    except Exception as e:
        _log("Weak dict error: %s" % e)
        import traceback
        _log(traceback.format_exc())

    if local_count > 0:
        _flush_attempts(worker_id, local_count, shared_state)
    _decrement_dict_active(shared_state)

def _process_enum_rule(worker_id: int, target: str, shared_state, rule_id: int, length: int) -> None:
    """处理枚举规则任务块（单个长度）"""
    generator = get_rule_generator(rule_id, length)
    if generator is None:
        _log("Generator for rule %d length %d is None" % (rule_id, length))
        _decrement_rule_active(shared_state)
        return
    
    local_count = 0
    
    try:
        for candidate in generator():
            if shared_state.is_terminated():
                break

            while shared_state.is_paused():
                if shared_state.is_terminated():
                    break
                time.sleep(0.05)

            if candidate == target:
                _log("FOUND PASSWORD: %s" % candidate)
                shared_state.set_found(candidate, worker_id)
                local_count += 1
                _flush_attempts(worker_id, local_count, shared_state)
                _decrement_rule_active(shared_state)
                return

            local_count += 1

            if local_count >= BATCH_SIZE:
                _flush_attempts(worker_id, local_count, shared_state)
                local_count = 0
    except Exception as e:
        _log("Generator error: %s" % e)
        import traceback
        _log(traceback.format_exc())

    if local_count > 0:
        _flush_attempts(worker_id, local_count, shared_state)
    _decrement_rule_active(shared_state)

def _flush_attempts(worker_id: int, count: int, shared_state) -> None:
    try:
        shared_state.add_attempts(worker_id, count)
        _log("Flushed %d attempts for worker %d" % (count, worker_id))
    except Exception as e:
        _log("Flush error: %s" % e)

def _decrement_dict_active(shared_state) -> None:
    """递减字典活跃worker计数器"""
    try:
        # 多进程模式（有 _task_lock 和 multiprocessing.Value）
        if hasattr(shared_state, '_task_lock'):
            with shared_state._task_lock:
                shared_state.dict_active_workers.value -= 1
        # 多线程模式（有 _lock 和普通整数）
        elif hasattr(shared_state, '_lock'):
            with shared_state._lock:
                shared_state.dict_active_workers -= 1
    except Exception as e:
        _log("Decrement dict active error: %s" % e)

def _decrement_rule_active(shared_state) -> None:
    """递减当前枚举规则活跃worker计数器"""
    try:
        if hasattr(shared_state, '_task_lock'):
            with shared_state._task_lock:
                shared_state.rule_active_workers.value -= 1
        elif hasattr(shared_state, '_lock'):
            with shared_state._lock:
                shared_state.rule_active_workers -= 1
    except Exception as e:
        _log("Decrement rule active error: %s" % e)
