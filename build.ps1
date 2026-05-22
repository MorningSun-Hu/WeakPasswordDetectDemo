$sep = "=" * 50

Write-Host $sep
Write-Host "  Windows 打包脚本 (uv 版本)"
Write-Host "  弱口令枚举暴力破解演示程序"
Write-Host $sep
Write-Host ""

# 检查 uv 是否安装
if (-Not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[错误] 未找到 uv 命令"
    Write-Host "请先安装 uv: https://docs.astral.sh/uv/getting-started/installation/"
    Write-Host "  PowerShell: irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit 1
}

# 检查 Python 3.13 free-threading
Write-Host "[1/5] 检查 Python 3.13 free-threading..."
uv python install 3.13t
Write-Host ""

# 安装依赖
Write-Host "[2/5] 安装项目依赖..."
uv sync --python 3.13t
Write-Host ""

# 安装 PyInstaller
Write-Host "[3/5] 安装打包工具 PyInstaller..."
uv add --python 3.13t pyinstaller
Write-Host ""

# 执行打包
Write-Host "[4/5] 执行打包 (使用 spec 文件)..."
uv run --python 3.13t pyinstaller --clean bruteforce.spec

if (-Not $?) {
    Write-Host "[错误] 打包失败!"
    pause
    exit 1
}

# 检查结果
Write-Host ""
Write-Host "[5/5] 打包完成!"
Write-Host ""
Write-Host "可执行文件位置: dist\WeakPasswordBruteForce.exe"
Write-Host ""

if (Test-Path "dist\WeakPasswordBruteForce.exe") {
    $file = Get-Item "dist\WeakPasswordBruteForce.exe"
    $sizeMB = [math]::Round($file.Length / 1MB, 2)
    Write-Host "文件大小: $sizeMB MB ($($file.Length) bytes)"
    Write-Host ""
    Write-Host "使用说明:"
    Write-Host "  双击 WeakPasswordBruteForce.exe 即可启动 Web 服务"
    Write-Host "  程序会自动打开默认浏览器访问 http://127.0.0.1:8000"
    Write-Host ""
} else {
    Write-Host "[警告] 未找到生成的 exe 文件"
}

Write-Host $sep
pause
