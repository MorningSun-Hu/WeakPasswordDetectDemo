"""核心引擎模块测试"""

import sys
import os
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brute_force.engine import BruteForceEngine


class MockCallback:
    def __init__(self):
        self.events = []

    def on_started(self, target_length, worker_count, cpu_count):
        self.events.append(("started", target_length, worker_count, cpu_count))

    def on_progress(self, status):
        self.events.append(("progress", status))

    def on_found(self, password, attempts, elapsed, worker_id):
        self.events.append(("found", password, attempts, elapsed, worker_id))

    def on_terminated(self, attempts, elapsed):
        self.events.append(("terminated", attempts, elapsed))

    def on_error(self, message):
        self.events.append(("error", message))


def test_engine_found():
    callback = MockCallback()
    engine = BruteForceEngine(worker_count=3, callback=callback)
    engine.start("7")
    
    # 检查 started 事件，现在有 4 个参数
    started_events = [e for e in callback.events if e[0] == "started"]
    assert len(started_events) == 1
    evt = started_events[0]
    assert evt[1] == 1  # target_length
    assert evt[2] == 3  # worker_count
    assert evt[3] > 0   # cpu_count
    
    assert any(e[0] == "found" for e in callback.events)
    
    found_event = [e for e in callback.events if e[0] == "found"][0]
    assert found_event[1] == "7"
    assert found_event[2] > 0  # attempts
    assert found_event[3] >= 0  # elapsed


def test_engine_get_status():
    engine = BruteForceEngine(worker_count=3)
    engine.shared_state.start_time = time.time() - 1.0
    status = engine.get_status()
    assert status["running"] == False
    assert "workers" in status
    assert len(status["workers"]) == 3
    assert status["elapsed"] >= 1.0


def test_engine_terminate():
    callback = MockCallback()
    engine = BruteForceEngine(worker_count=3, callback=callback)
    
    # 使用一个极难猜到的长密码，确保在规定时间内能触发终止
    import threading
    t = threading.Thread(target=engine.start, args=("ZZZZZZZZZZZZZZZZ",))
    t.start()
    
    time.sleep(0.2)
    engine.terminate()
    t.join(timeout=2.0)
    
    # 终止后状态应为非运行
    assert engine._running == False
    assert engine.shared_state.is_terminated()


if __name__ == "__main__":
    test_engine_found()
    test_engine_get_status()
    test_engine_terminate()
    print("engine 测试全部通过")
