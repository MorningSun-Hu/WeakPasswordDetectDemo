@echo off
echo ============================================
echo   Windows 打包脚本
echo   弱口令枚举暴力破解演示程序
echo ============================================
echo.

REM 检查 Python 3.13 free-threading 版本
python3.13t --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 未找到 python3.13t
    echo 请先安装 Python 3.13 free-threading 版本:
    echo   1. 下载: https://www.python.org/downloads/
    echo   2. 选择 Free-threading 构建版本 (python3.13t.exe)
    echo   3. 或将 python3.13t 添加到 PATH
    echo.
    echo 如果使用 uv，可运行:
    echo   uv python install 3.13t
    pause
    exit /b 1
)

echo [1/4] 检测环境...
python3.13t --version
echo.

echo [2/4] 安装依赖...
python3.13t -m pip install pyinstaller --quiet
echo 依赖安装完成.
echo.

echo [3/4] 执行打包...
python3.13t -m PyInstaller ^
    --onefile ^
    --name "弱口令破解演示" ^
    --add-data "pyproject.toml;." ^
    --clean ^
    main.py

if %errorlevel% neq 0 (
    echo [错误] 打包失败!
    pause
    exit /b 1
)

echo.
echo [4/4] 打包完成!
echo.
echo 可执行文件位置:
echo   dist\弱口令破解演示.exe
echo.
echo 文件大小:
dir /B /-C dist\弱口令破解演示.exe 2>nul
echo.
echo 可直接双击运行，无需安装 Python.
echo ============================================
pause
