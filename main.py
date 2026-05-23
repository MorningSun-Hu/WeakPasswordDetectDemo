"""程序入口

默认启动 Web 服务并自动打开浏览器访问。
支持 Windows 打包为独立 exe。
"""

import sys
import os
import argparse
import multiprocessing
import webbrowser
import socket
import time
from threading import Thread

from brute_force.cli import run_cli


def find_free_port(start_port: int = 8000, end_port: int = 8100) -> int:
    """查找可用端口"""
    for port in range(start_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    return 8000


def run_web_server(port: int):
    """运行 Web 服务器"""
    import uvicorn
    from brute_force.server import app
    
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")


def main():
    """主入口函数"""
    multiprocessing.freeze_support()

    parser = argparse.ArgumentParser(description="弱口令枚举暴力破解演示程序")
    parser.add_argument("--cli", action="store_true", help="启动 CLI 模式 (默认启动 Web 模式)")
    args = parser.parse_args()

    if args.cli:
        run_cli()
        return

    # 查找可用端口
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"
    
    # 控制台提示
    print("=" * 50)
    print("  弱口令枚举暴力破解演示程序 (Web 版) v1.0.1")
    print("=" * 50)
    print(f"服务地址: {url}")
    print("正在打开浏览器...")
    print("按 Ctrl+C 停止服务")
    print("=" * 50)
    
    # 延迟打开浏览器（等待服务器启动）
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(url)
    
    browser_thread = Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # 启动 Web 服务器
    try:
        run_web_server(port)
    except KeyboardInterrupt:
        print("\n服务已停止。")
        sys.exit(0)


if __name__ == "__main__":
    main()
