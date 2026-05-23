"""共享状态模块测试"""

import sys
import os
import time
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brute_force.shared_state import create_shared_state


def test_initial_state():
    state = create_shared_state(3, use_multiprocessing=False)
    assert state.found == False
    assert state.terminate_flag == False
    assert state.get_total_attempts() == 0
    assert state.get_elapsed() == 0.0


def test_set_and_get_found_password():
    state = create_shared_state(3, use_multiprocessing=False)
    state.set_found("test123", 1)
    assert state.found == True
    assert state.get_found_password() == "test123"
    assert state.found_worker_id == 1


def test_reset():
    state = create_shared_state(3, use_multiprocessing=False)
    state.set_found("pass", 0)
    state.terminate()
    state.reset(3)
    assert state.found == False
    assert state.get_found_password() == ""
    assert state.terminate_flag == False
    assert state.found_worker_id == -1


def test_add_attempts():
    state = create_shared_state(3, use_multiprocessing=False)
    state.add_attempts(0, 100)
    state.add_attempts(1, 200)
    assert state.get_total_attempts() == 300
    assert state.attempts[0] == 100
    assert state.attempts[1] == 200


def test_terminate():
    state = create_shared_state(3, use_multiprocessing=False)
    assert state.is_terminated() == False
    state.terminate()
    assert state.is_terminated() == True


def test_elapsed_time():
    state = create_shared_state(3, use_multiprocessing=False)
    state.start_time = time.time() - 5.5
    elapsed = state.get_elapsed()
    assert 5.0 <= elapsed <= 6.0


def test_thread_safety():
    """多线程并发写入共享状态，验证锁是否生效"""
    state = create_shared_state(3, use_multiprocessing=False)
    errors = []

    def worker(worker_id, count):
        try:
            for _ in range(count):
                state.add_attempts(worker_id, 1)
        except Exception as e:
            errors.append(str(e))

    threads = [threading.Thread(target=worker, args=(i, 10000)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, "并发测试出现异常: %s" % errors
    assert state.get_total_attempts() == 30000


def test_dict_rule_completes_before_next_rule():
    state = create_shared_state(3, use_multiprocessing=False)
    state.set_dict_total(10)

    first = state.get_next_task(worker_count=3, max_len=8)
    assert first[0] == 0

    waiting = state.get_next_task(worker_count=3, max_len=8)
    assert waiting == (0, -1, -1)

    state.dict_active_workers -= 1
    next_task = state.get_next_task(worker_count=3, max_len=8)
    assert next_task == (1, 1, 1)


def test_enum_rule_completes_before_next_rule():
    state = create_shared_state(3, use_multiprocessing=False)
    state.set_dict_total(0)

    first_enum = state.get_next_task(worker_count=3, max_len=2)
    second_enum = state.get_next_task(worker_count=3, max_len=2)
    assert first_enum == (1, 1, 1)
    assert second_enum == (1, 2, 2)

    waiting = state.get_next_task(worker_count=3, max_len=2)
    assert waiting == (0, -1, -1)

    state.rule_active_workers -= 1
    still_waiting = state.get_next_task(worker_count=3, max_len=2)
    assert still_waiting == (0, -1, -1)

    state.rule_active_workers -= 1
    next_rule = state.get_next_task(worker_count=3, max_len=2)
    assert next_rule == (2, 1, 1)


def test_terminated_state_returns_exit_signal():
    state = create_shared_state(3, use_multiprocessing=False)
    state.terminate()
    assert state.get_next_task(worker_count=3, max_len=8) == (None, -1, -1)


if __name__ == "__main__":
    test_initial_state()
    test_set_and_get_found_password()
    test_reset()
    test_add_attempts()
    test_terminate()
    test_elapsed_time()
    test_thread_safety()
    test_dict_rule_completes_before_next_rule()
    test_enum_rule_completes_before_next_rule()
    test_terminated_state_returns_exit_signal()
    print("shared_state 测试全部通过")
