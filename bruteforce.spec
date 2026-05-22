# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置文件"""

import os

block_cipher = None

# 收集静态文件
static_dir = os.path.join(os.path.dirname(__file__), 'brute_force', 'static')
static_files = []
for root, dirs, files in os.walk(static_dir):
    for file in files:
        full_path = os.path.join(root, file)
        rel_path = os.path.relpath(full_path, os.path.dirname(__file__))
        static_files.append((full_path, os.path.dirname(rel_path)))

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
        'uvicorn.loops.auto',
        'uvicorn.lifespan.on',
        'fastapi',
        'fastapi.middleware.cors',
        'fastapi.staticfiles',
        'fastapi.responses',
        'pydantic',
        'psutil',
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
