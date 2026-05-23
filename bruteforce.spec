# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置文件"""

import os

block_cipher = None

# 获取项目根目录（spec 文件所在目录）
project_root = os.path.dirname(SPEC)

# 收集静态文件
static_dir = os.path.join(project_root, 'brute_force', 'static')
static_files = []
for root, dirs, files in os.walk(static_dir):
    for file in files:
        full_path = os.path.join(root, file)
        rel_path = os.path.relpath(full_path, project_root)
        static_files.append((full_path, os.path.dirname(rel_path)))

# 收集弱口令库数据文件
data_file = os.path.join(project_root, 'brute_force', 'data', 'weak_passwords.txt')
if os.path.exists(data_file):
    static_files.append((data_file, os.path.join('brute_force', 'data')))

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=static_files,
    hiddenimports=[
        'brute_force',
        'brute_force.engine',
        'brute_force.enum_rules',
        'brute_force.worker',
        'brute_force.shared_state',
        'brute_force.ws_manager',
        'brute_force.schemas',
        'brute_force.callback',
        'brute_force.utils',
        'brute_force.server',
        'uvicorn',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.ws.auto',
        'uvicorn.loops.auto',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        'fastapi.responses',
        'pydantic',
        'psutil',
        'websockets',
        'websockets.legacy',
        'websockets.server',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='WeakPasswordBruteForce',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
