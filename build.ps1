$sep = "=" * 44

Write-Host $sep
Write-Host "  Windows 打包脚本 (uv 版本)"
Write-Host "  弱口令枚举暴力破解演示程序"
Write-Host $sep
Write-Host ""

if (-Not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "[错误] 未找到 uv 命令"
    Write-Host "请先安装 uv: https://docs.astral.sh/uv/getting-started/installation/"
    Write-Host "  PowerShell: irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit 1
}

Write-Host "[1/4] 安装 Python 3.13 free-threading..."
uv python install 3.13t
Write-Host ""

Write-Host "[2/4] 安装打包依赖..."
uv add --python 3.13t pyinstaller
Write-Host ""

Write-Host "[3/4] 执行打包..."
uv run --python 3.13t pyinstaller --onefile --name WeakPasswordBruteForce --clean main.py

if (-Not $?) {
    Write-Host "[错误] 打包失败!"
    pause
    exit 1
}

Write-Host ""
Write-Host "[4/4] 打包完成!"
Write-Host ""
Write-Host "可执行文件位置: dist\WeakPasswordBruteForce.exe"
Write-Host ""
if (Test-Path "dist\WeakPasswordBruteForce.exe") {
    $file = Get-Item "dist\WeakPasswordBruteForce.exe"
    Write-Host "文件大小: " $file.Length " bytes"
}
Write-Host ""
Write-Host $sep
pause
